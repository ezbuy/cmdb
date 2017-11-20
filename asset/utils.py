# coding=utf-8
import re

from asset.models import *
from asset import models
import os,time,commands,json,requests
from salt.client import LocalClient
from logs.models import goLog,publishLog
from celery.task import task
import xmlrpclib
from salt_api.api import SaltApi
from mico.settings import dingding_api,crontab_api,dingding_robo_url
from functools import wraps
from django.contrib.auth.models import User
from ipaddress import IPv4Address, IPv4Network
salt_api = SaltApi()


def logs(user,ip,action,result):
    goLog.objects.create(user=user, remote_ip=ip, goAction=action, result=result)

def publish_logs(user,ip,url,result):
    publishLog.objects.create(user=user, remote_ip=ip, publish_url=url, publish_result=result)


def get_rev_latest(name):

    rl = models.GoServiceRevision.objects.filter(name=name).order_by('-id').first()

    if rl:
        result = []
        result.append(rl.last_rev)
        result.append(rl.gotemplate_last_rev)
        return result
    else:
        return False


def update_rev_latest(name, goproject_rev, gotemplate_rev):
    # rl = models.GoServiceRevision.objects.filter(name=name).first()
    # if not rl:
    #     rl = GoServiceRevision()

    rl = GoServiceRevision()
    rl.name = name
    rl.last_rev = goproject_rev
    rl.gotemplate_last_rev = gotemplate_rev
    rl.last_clock = int(time.time())
    rl.save()


def get_service_status(service_name):
    # Go Service model instance
    _srv = goservices.objects.filter(name=service_name)
    if not _srv:
        return False

    # Supervisord model instance
    for i in _srv:
        _svd = gostatus.objects.filter(hostname=i.saltminion.id).first()
        try:
            s = xmlrpclib.Server('http://%s:%s@%s:%s/RPC2' % (_svd.supervisor_username, _svd.supervisor_password,
                                                              _svd.supervisor_host, _svd.supervisor_port))
            info = s.supervisor.getProcessInfo(service_name)
            if info['state'] in [30,100,200,1000]:
                return False
            else:
                return True
        except Exception, e:
            print e
            return True


def get_svn_revision(svn_log):
    try:
        for _, v in svn_log.items():
            m = re.search('---+\nr(?P<rev>\d+)\s+\|\s+', v)
            if m:
                rev_head = m.group('rev')
                return rev_head
    except Exception as e:
        print str(e)
        return False


class goPublish:
    def __init__(self,env):
        self.env = env
        self.saltCmd = LocalClient()
        self.svnInfo = models.svn.objects.all()


    def getNowTime(self):
        return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(time.time()))

    def deployGo(self,name,services,username,ip,tower_url,phone_number,svn_revision='head',gotemplate_svn_revision='head'):

        self.name = name          # Go project name
        self.services = services  # Go service name
        self.username = username
        self.ip = ip
        self.tower_url = tower_url
        self.phone_number = phone_number
        self.svn_revision = svn_revision
        self.gotemplate_svn_revision = gotemplate_svn_revision
        hostInfo = {}
        result = []

        rev_head = None

        #minionHost = commands.getstatusoutput('salt-key -l accepted')[1].split()[2:]

        services_info = goservices.objects.filter(env=self.env).filter(name=self.services)
        for s in services_info:
            go_template = GOTemplate.objects.filter(project=s.group).filter(hostname=s.saltminion).first()
            # update conf file
            if go_template:
                svn_gotemplate = self.saltCmd.cmd('%s' % s.saltminion.saltname, 'cmd.run',
                    ['svn update -r%s --username=%s --password=%s --non-interactive %s && svn log -l 1 --username=%s --password=%s --non-interactive %s'
                    % (self.gotemplate_svn_revision, go_template.username, go_template.password, go_template.localpath, go_template.username, go_template.password, go_template.localpath)])
            else:
                svn_gotemplate = {'Warning':'#####################Not gotemplate file######################'}
            result.append(svn_gotemplate)
            for p in self.svnInfo:
                if p.project.name == self.name:
                    deploy_pillar = "pillar=\"{'project':'" + self.name + "'}\""
                    os.system("salt '%s' state.sls logs.gologs %s" % (s.saltminion.saltname, deploy_pillar))
                    currentTime = self.getNowTime()

                    # move go binary
                    self.saltCmd.cmd('%s' % s.saltminion.saltname, 'cmd.run',['mv %s %s/%s_%s' % (p.executefile, p.movepath,self.name, currentTime)])
                    # deploy go project
                    svn = self.saltCmd.cmd('%s' % s.saltminion.saltname, 'cmd.run',
                        ['svn update -r%s --username=%s --password=%s --non-interactive %s && svn log -l 1 --username=%s --password=%s --non-interactive %s'
                        % (self.svn_revision,p.username, p.password, p.localpath, p.username, p.password, p.localpath)])
                    result.append(svn)
            restart = self.saltCmd.cmd('%s' % s.saltminion.saltname,'cmd.run',['supervisorctl restart %s' % self.services])
            result.append(restart)


            info = self.name + "(" + tower_url + ")"
            if self.svn_revision == 'head':
                action = 'deploy ' + info
                dingding_robo(s.saltminion.saltname,info,restart,self.username,self.phone_number,types=1)
            else:
                action = 'revert ' + info
                dingding_robo(s.saltminion.saltname, info, restart, self.username, self.phone_number, types=3)

        print '-------------------svn:',self.svn_revision
        logs(self.username,self.ip,action,result)
        publish_logs(self.username,self.ip,self.tower_url,result)

        if self.svn_revision == 'head':
            # ROLLBACK to last successful revision if failed
            if not get_service_status(services):
                goservice_rev_last = get_rev_latest(self.name)
                print '#####goservice_rev_last.gotemplate_last_rev',goservice_rev_last
                if goservice_rev_last:
                    revert_info = {'Warning':'#####################Roll back to the previous version######################'}
                    result.append(revert_info)
                    result += self.deployGo(self.name, self.services, self.username, self.ip, self.tower_url, self.phone_number, svn_revision=goservice_rev_last[0], gotemplate_svn_revision=goservice_rev_last[1])
            else:
                try:
                    # get head revision from svn
                    rev_head = get_svn_revision(svn)
                    gotemplate_rev_head = get_svn_revision(svn_gotemplate)
                    update_rev_latest(self.name, rev_head, gotemplate_rev_head)
                except Exception as e:
                    print str(e)
                    result.append({'save head revision FAILED': str(e)})

        return result

    def go_revert(self,project,revertFile,host,username,ip):

        self.project = project
        self.revertFile = revertFile
        self.host = host
        self.username = username
        self.ip = ip
        result = []

        for p in self.svnInfo:
            if p.project.name == self.project:
                currentTime = self.getNowTime()
                rename = p.revertpath + '_revert_' + currentTime
                runCmd = "'mv " + p.executefile + " " + rename + "'"


                os.system("salt %s state.sls logs.revert" % self.host)
                self.saltCmd.cmd('%s' % self.host,'cmd.run',['%s' % runCmd])
                revertResult = commands.getstatusoutput("salt '%s' cmd.run 'cp %s/%s %s'" %(self.host,p.movepath,self.revertFile,p.executefile))

                if revertResult[0] == 0:
                    for obj in goservices.objects.filter(env=self.env):
                        if obj.group.name == self.project and self.host == obj.saltminion.saltname:
                            restart = self.saltCmd.cmd('%s' % self.host,'cmd.run',['supervisorctl restart %s' % obj.name])
                            result.append(restart)

                    mes = 'revert to %s version is successful.' % revertFile
                    #mes = {self.host:mes}
                    #result.append(mes)
                else:
                    mes = 'revert to %s version is failed.' % revertFile

                mes = {self.host: mes}
                info = 'revert ' + self.project
                dingding_robo(self.host,info,mes,username)

                result.append(mes)

        action = 'revert ' + self.project
        logs(self.username, self.ip, action, result)
        return result


    def goConf(self,project,usernmae,ip,phone_number):
        self.project = project
        self.username = usernmae
        self.ip = ip
        self.phone_number = phone_number
        result = []
        conf = goconf.objects.all()



        for p in conf:
            try:
                if str(p.env) == self.env and p.project.name == self.project:
                    #print p.username,p.password,p.localpath,p.hostname
                    confCmd = "svn update --username=%s --password=%s --non-interactive %s" %(p.username,p.password,p.localpath)
                    confResult = self.saltCmd.cmd('%s' % p.hostname,'cmd.run',['%s' % confCmd])
                    result.append(confResult)

                    info = self.project + ' conf'

                    dingding_robo(p.hostname, info, confResult, self.username,self.phone_number)
            except Exception,e:
                print e
        action = 'conf ' + self.project
        logs(self.username, self.ip, action, result)


        return result


    def build_go(self,hostname,project,supervisorName,goCommand,svnRepo,svnUsername,svnPassword,fileName,username,ip):
        self.hostname = hostname
        self.project = project
        self.supervisorName = supervisorName
        self.goCommand = goCommand
        self.svnRepo = svnRepo
        self.svnUsername = svnUsername
        self.svnPassword = svnPassword
        self.fileName = fileName
        self.username = username
        self.ip =  ip

        f = open(self.fileName,'w')
        f.write("start....")
        f.write('\n\n\n\n')
        f.flush()
        #result = self.saltCmd.cmd(self.hostname, 'state.sls', kwarg={
        #    'mods': 'goservices.supervisor_submodule',
        #    'pillar': {
        #        'goprograme': self.project,
        #        'supProgrameName': self.supervisorName,
        #        'goRunCommand': self.goCommand,
        #        'svnrepo': self.svnRepo,
        #        'svnusername': self.svnUsername,
        #        'svnpassword': self.svnPassword,
        #    },
        #})
        try:
            pillar= " pillar=\"{'goprograme': '%s','supProgrameName': '%s','goRunCommand': '%s','svnrepo': '%s','svnusername': '%s','svnpassword': '%s'}\"" % (self.project,self.supervisorName,self.goCommand,self.svnRepo,self.svnUsername,self.svnPassword)
            deploy_cmd = "salt " + self.hostname +  " state.sls queue=True goservices.supervisor_submodule " + pillar
            s, result = commands.getstatusoutput(deploy_cmd)
            f.write(result)
            f.write('\n\n\n\n')
            f.write('done')
            f.close()
            if result.find('Failed:    0') < 0:
                dingding_robo(self.hostname,'add ' + self.project + ' service','is error',self.username)
                logs(self.username,self.ip,'add ' + self.project + ' service' ,'Failed')
            else:
                dingding_robo(self.hostname, 'add ' + self.project + ' service', 'successful', self.username)
                logs(self.username, self.ip,'add ' + self.project + ' service', 'Successful')
        except Exception, e:
            print e
            return 'error'

        return result

    def go_template(self, project, usernmae, ip, phone_number):
        self.project = project
        self.username = usernmae
        self.ip = ip
        self.phone_number = phone_number
        result = []
        conf = GOTemplate.objects.all()

        for p in conf:
            try:
                if str(p.env) == self.env and p.project.name == self.project:
                    confCmd = "svn checkout %s --username=%s --password=%s --non-interactive %s" % (
                    p.repo,p.username, p.password, p.localpath)
                    confResult = self.saltCmd.cmd('%s' % p.hostname, 'cmd.run', ['%s' % confCmd])
                    result.append(confResult)
                    info = self.project + ' template'
                    dingding_robo(p.hostname, info, confResult, self.username,self.phone_number)
            except Exception, e:
                print e
        action = self.project + ' template'
        logs(self.username, self.ip, action, result)

        return result
class goServicesni:
    def __init__(self,projectName):
        self.projectName = projectName

    def getServiceName(self):
        services = []
        if self.projectName:
            groupname = gogroup.objects.get(name=self.projectName)
            services = goservices.objects.filter(group=groupname).order_by('name')
        return services




def syncAsset():
    data = {
        'client': 'local',
        'tgt': '*',
        'fun': 'grains.items',
    }
    result = salt_api.salt_cmd(data)
    if result != 0:
        result = result['return']

    #print result

    try:
        subnet = IPv4Network(u'172.16.0.0/12')
        for r in result:
            for host,info in r.items():
                if '127.0.0.1' in info['ipv4']:
                    info['ipv4'].remove('127.0.0.1')
                for h in info['ipv4'][:]:
                    ips = IPv4Address(u'%s' % h)
                    if ips in subnet:
                        info['ipv4'].remove(h)
                ip = info['ipv4']
                hostname_id = host
                cpu = info['cpu_model']
                memory = info['mem_total']
                if info.has_key('virtual'):
                    asset_type = info['virtual']
                else:
                    asset_type = 'physical'
                if info.has_key('osfinger'):
                    os = info['osfinger']
                else:
                    os = info['osfullname']
                print '---%s-%s--' %(ip,hostname_id)

                try:
                    if not Asset.objects.filter(hostname=hostname_id):
                        Asset.objects.create(ip=ip,hostname=hostname_id,system_type=os,cpu=cpu,memory=memory,asset_type=asset_type)
                except Exception,e:
                    print e
    except Exception,e:
        print e




class go_monitor_status(object):
    def get_hosts(self):
        obj = gostatus.objects.all()
        return obj

    def get_supervisor_status(self,hostname_id):
        self.hostname_id = hostname_id
        obj = gostatus.objects.all().filter(hostname_id=self.hostname_id)
        for info in obj:
            try:
                s = xmlrpclib.Server('http://%s:%s@%s:%s/RPC2' % (info.supervisor_username,info.supervisor_password,info.supervisor_host,info.supervisor_port))
                status = s.supervisor.getAllProcessInfo()
            except Exception, e:
                print e
                return 0

        return status

class crontab_svn_status(object):
    def __init__(self,login_user,ip):
        self.login_user = login_user
        self.ip = ip
    def get_crontab_list(self):
        obj = crontab_svn.objects.all()
        return obj

    def crontab_svn_update(self,hostname,project,phone_number):
        self.hostname = hostname
        self.project = project
        self.phone_number = phone_number
        host = minion.objects.get(saltname=self.hostname)
        obj = crontab_svn.objects.get(hostname=host,project=self.project)

        cmd = ["svn checkout %s %s --username=%s --password=%s --non-interactive " % (obj.repo,obj.localpath,obj.username, obj.password),'env={"LC_ALL": "en_US.UTF-8"}']
        data = {
            'client': 'local',
            'tgt': self.hostname,
            'fun': 'cmd.run',
            'arg': cmd
        }
        result = salt_api.salt_cmd(data)
        if result != 0:
            result = result['return']
        dingding_robo(self.hostname,self.project + " repo",result,self.login_user,self.phone_number)
        logs(self.login_user,self.ip,'update svn',result)
        return result



@task
def deploy_go(env,hostname,project,supervisorName,goCommand,svnRepo,svnUsername,svnPassword,fileName,username,ip):
    obj = goPublish(env)
    obj.build_go(hostname, project, supervisorName, goCommand, svnRepo, svnUsername, svnPassword,fileName,username,ip)

def getNowTime():
    return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(time.time()))


def get_cronjob_list():
    url = crontab_api
    print '----',url
    params = {
        'fun': 'list'
    }
    headers = {'Content-Type': 'application/json'}
    try:
        obj = requests.post(url=url, headers=headers, data=json.dumps(params)).text
        obj = json.loads(obj)
        return obj['result']
    except Exception, e:
        print e
        return 0

class go_action(object):   #go "start,stop,restart" action
    def __init__(self,service,user,ip):
        self.service = service
        self.user = user
        self.ip = ip
        self.result = {}


    def start(self):
        obj = goservices.objects.filter(name=self.service)
        for info in obj:
            supervisor_info = gostatus.objects.get(hostname=info.saltminion_id)
            supervisor_obj = xmlrpclib.Server('http://%s:%s@%s:%s/RPC2' % (
                supervisor_info.supervisor_username, supervisor_info.supervisor_password,
                supervisor_info.supervisor_host, supervisor_info.supervisor_port))
            if supervisor_obj.supervisor.getProcessInfo(self.service)['state'] != 20:
                supervisor_obj.supervisor.startProcess(self.service)
            if supervisor_obj.supervisor.getProcessInfo(self.service)['state'] == 20:
                dingding_robo(info.saltminion,'start "%s" service' % self.service,'successful',self.user)
                logs(self.user, self.ip, 'start "%s" service' % self.service, 'successful')
                self.result[str(info.saltminion)] = 'successful'
            else:
                dingding_robo(info.saltminion, 'start "%s" service' % self.service, 'is error', self.user)
                logs(self.user, self.ip, 'start "%s" service' % self.service , 'failed')
                self.result[str(info.saltminion)] = 'failed'
        return  self.result


    def stop(self):
        obj = goservices.objects.filter(name=self.service)
        for info in obj:
            supervisor_info = gostatus.objects.get(hostname=info.saltminion_id)
            supervisor_obj = xmlrpclib.Server('http://%s:%s@%s:%s/RPC2' % (
                supervisor_info.supervisor_username, supervisor_info.supervisor_password,
                supervisor_info.supervisor_host, supervisor_info.supervisor_port))
            if supervisor_obj.supervisor.getProcessInfo(self.service)['state'] != 0:
                supervisor_obj.supervisor.stopProcess(self.service)
            if supervisor_obj.supervisor.getProcessInfo(self.service)['state'] == 0:
                dingding_robo(info.saltminion, 'stop "%s" service' % self.service, 'successful', self.user)
                logs(self.user,self.ip,'stop "%s" service' % self.service,'successful')
                self.result[str(info.saltminion)] = 'successful'
            else:
                dingding_robo(info.saltminion, 'stop "%s" service' % self.service, 'is error', self.user)
                logs(self.user, self.ip, 'stop "%s" service' % self.service, 'failed')
                self.result[str(info.saltminion)] = 'failed'
        return self.result

    def restart(self):
        obj = goservices.objects.filter(name=self.service)
        for info in obj:
            supervisor_info = gostatus.objects.get(hostname=info.saltminion_id)
            supervisor_obj = xmlrpclib.Server('http://%s:%s@%s:%s/RPC2' % (
                supervisor_info.supervisor_username, supervisor_info.supervisor_password,
                supervisor_info.supervisor_host, supervisor_info.supervisor_port))
            if supervisor_obj.supervisor.getProcessInfo(self.service)['state'] != 0:
                supervisor_obj.supervisor.stopProcess(self.service)
            supervisor_obj.supervisor.startProcess(self.service)
            if supervisor_obj.supervisor.getProcessInfo(self.service)['state'] == 20:
                dingding_robo(info.saltminion, 'restart "%s" service' % self.service, 'successful', self.user)
                logs(self.user, self.ip, 'restart "%s" service' % self.service, 'successful')
                self.result[str(info.saltminion)] = 'successful'
            else:
                dingding_robo(info.saltminion, 'restart "%s" service' % self.service, 'is error', self.user)
                logs(self.user, self.ip, 'restart "%s" service' % self.service, 'failed')
                self.result[str(info.saltminion)] = 'failed'
        return self.result




def deny_resubmit(page_key=''):
    def decorator(func):
        @wraps(func)
        def _wrapped_view(request, *args, **kwargs):
            if request.method == 'GET':
                request.session['%s_submit' % page_key] = str(time.time())
                print 'session: ', request.session['%s_submit' % page_key]
            elif request.method == 'POST':
                old_key = request.session.get('%s_submit' % page_key, '')
                if old_key == '':
                    from django.http import HttpResponseRedirect
                    return HttpResponseRedirect('/')
                request.session['%s_submit' % page_key] = ''

                user = User.objects.get(username=request.user)
                try:
                    phone_number = UserProfile.objects.get(user=user).phone_number
                except Exception, e:
                    print e
                    phone_number = ''
                post_dict = request.POST
                post_dict = post_dict.copy()
                post_dict.update({'phone_number':phone_number})
                request.POST = post_dict
            return func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def dingding_robo(hostname='',project='',result='',username='',phone_number='',types=1,info=''):
    url = dingding_robo_url
    headers = {'Content-Type': 'application/json'}
    hs = str(hostname) + " by " + str(username)

    try:
        if type(result) == dict:
            if result.values()[0].find('ERROR') > 0 or result.values()[0].find('error') > 0 or result.values()[0].find('Skip') > 0:
                errmsg = 'Failed'
            else:
                errmsg = 'Success'
        elif type(result) == list:
            result = str(result)
            if result.find('ERROR') > 0 or result.find('error') > 0 or result.find('Skip') > 0:
                errmsg = 'Failed'
            else:
                errmsg = 'Success'
        elif type(result) == str:
            if result.find('ERROR') > 0 or result.find('error') > 0 or result.find('Skip') > 0:
                errmsg = 'Failed'
            else:
                errmsg = 'Success'
    except Exception, e:
        print e
        errmsg = 'Failed'
    current_time = getNowTime()
    if types == 1:
        content = current_time + " " + errmsg + ": " + "deploy " + str(project) + " to " + str(hostname) + " by " + str(username)
    elif types == 2:
        content = current_time + ": " + info
    elif types == 3:
        content = current_time + " " + errmsg + ": " + "revert " + str(project) + " to " + str(hostname) + " by " + str(username)

    data ={
        "msgtype": "text",
        "text": {
            "content": content
            },
        "at": {
            "atMobiles": [
            phone_number
             ],
             }
        }
    print data
    try:
        requests.post(url,headers=headers,data=json.dumps(data),timeout=3)
    except Exception,e:
        print e
