# coding=utf-8
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

salt_api = SaltApi()


def logs(user,ip,action,result):
    goLog.objects.create(user=user, remote_ip=ip, goAction=action, result=result)

def publish_logs(user,ip,url,result):
    publishLog.objects.create(user=user, remote_ip=ip, publish_url=url, publish_result=result)


class goPublish:
    def __init__(self,env):
        self.env = env
        self.saltCmd = LocalClient()
        self.svnInfo = models.svn.objects.all()


    def getNowTime(self):
        return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(time.time()))


    def deployGo(self,name,services,username,ip,tower_url,phone_number):

        self.name = name
        self.services = services
        self.username = username
        self.ip = ip
        self.tower_url = tower_url
        self.phone_number = phone_number
        hostInfo = {}
        result = []



        minionHost = commands.getstatusoutput('salt-key -l accepted')[1].split()[2:]


        groupname = gogroup.objects.all()
        for name in groupname:
            if self.name == name.name:
                for obj in goservices.objects.filter(env=self.env).filter(group_id=name.id):
                    for saltname in minion.objects.filter(id=obj.saltminion_id):
                        saltHost = saltname.saltname
                        if saltHost not in minionHost:
                            notMinion = 'No minions matched the %s host.' % saltHost
                            result.append(notMinion)
                        if obj.name == self.services:
                            golist = [self.services]
                            hostInfo[saltHost] = golist

        for host, goname in hostInfo.items():
            for p in self.svnInfo:
                if p.project.name == self.name:
                    deploy_pillar = "pillar=\"{'project':'" + self.name + "'}\""
                    os.system("salt '%s' state.sls logs.gologs %s" % (host, deploy_pillar))
                    currentTime = self.getNowTime()
                    self.saltCmd.cmd('%s' % host, 'cmd.run',['mv %s %s/%s_%s' % (p.executefile, p.movepath,self.name, currentTime)])
                    svn = self.saltCmd.cmd('%s' % host, 'cmd.run', ['svn update --username=%s --password=%s --non-interactive %s' % (p.username, p.password, p.localpath)])
                    result.append(svn)


            allServices = " ".join(goname)
            restart = self.saltCmd.cmd('%s'%host,'cmd.run',['supervisorctl restart %s'%allServices])
            result.append(restart)

            info = self.name + "(" + tower_url + ")"
            dingding_robo(host,info,restart,self.username,self.phone_number)

        action = 'deploy ' + info
        logs(self.username,self.ip,action,result)
        publish_logs(self.username,self.ip,self.tower_url,result)


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
        groupname = gogroup.objects.all()
        for group in groupname:
            if self.projectName == group.name:
                for obj in goservices.objects.filter(group=group.id):
                    services.append(obj)

        return services





def syncAsset():
    salt = LocalClient()
    grains = salt.cmd('*','grains.items')
    obj = Asset.objects.all()
    host_list = []
    for i in obj:
        host_list.append(i.hostname)


    try:
        for host in grains.keys():
            ip = grains[host]['ipv4'][-1]
            hostname_id = grains[host]['id']
            cpu = grains[host]['cpu_model']
            memory = grains[host]['mem_total']
            if grains[host].has_key('virtual'):
                asset_type = grains[host]['virtual']
            else:
                asset_type = 'physical'
            if grains[host].has_key('osfinger'):
                os = grains[host]['osfinger']
            else:
                os = grains[host]['osfullname']


            if host not in host_list:
                try:
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



def dingding_robo(hostname,project,result,username,phone_number=''):
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
    content = current_time + " " + errmsg + ": " + "deploy " + str(project) + " to " + str(hostname) + " by " + str(username)
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