import os,time,commands,json
from salt.client import LocalClient
from www.models import *
from celery.task import task
from asset.utils import logs,dingding_robo
from mico.settings import nginx_api
import requests
from salt_api.api import SaltApi





salt_api = SaltApi()
class wwwFun:
    def __init__(self,env,username,ip,fileName,phone_number):
        self.env = env
        self.username = username
        self.ip = ip
        self.fileName = fileName
        self.f = open(self.fileName,'w')
        self.result = []
        self.phone_number = phone_number




    def __nginx_backup(self,hosts,block_ip,block_server,nginx_upstream,is_block):
        self.hosts = hosts
        self.block_ip =block_ip
        self.block_server = block_server
        self.nginx_upstream = nginx_upstream
        upstream_host = ''

        try:
            for ip in self.hosts:
                if is_block == 1:
                    upstream_host += 'server %s; ' % ip;
                else:
                    if len(self.hosts) == 1:
                        upstream_host += 'server %s; ' % ip;
                    elif ip != self.block_ip:
                        upstream_host += 'server %s; ' % ip;
            if not upstream_host:
                print 'not upstream_host!!!!'
                exit()

            for lb in nginx_api:
                url = "%s/upstream/%s" % (lb, self.nginx_upstream)
                r=requests.post(url,data=upstream_host)

                if r.text != 'success':
                    exit()
                r = requests.get(url)
                print r.text
            return 0
        except Exception,e:
            print e
            self.f.write('error')
            self.f.close()
            dingding_robo(self.block_server, self.site, 'is error', self.username, self.phone_number)
            logs(self.username, self.ip, self.site, 'Failed')
            return 1




    def __svn_update(self,web_server,svn_path,svn_username,svn_password,svn_revision):
        self.web_server = web_server
        self.svn_path = svn_path
        self.svn_username = svn_username
        self.svn_password = svn_password
        self.svn_revision = svn_revision


        try:  #####svn update########
            update_cmd = 'svn update -r %s %s --username=%s --password=%s' % (self.svn_revision,self.svn_path, self.svn_username, self.svn_password)

            print '-----svn----',update_cmd
            data = {
                'client': 'local',
                'tgt': self.web_server,
                'fun': 'cmd.run',
                'arg': update_cmd
            }
            update = salt_api.salt_cmd(data)
            print update
            if update['return'][0][self.web_server].find('Error') > 0 or update['return'][0][self.web_server].find('error') > 0:
                print "!!!!!!!!!!!!!!!!!! [update svn] ERROR !!!!!!!!!!!!!!!!!!!"
                return 1
        except Exception, e:
            print e
            self.f.write('error')
            self.f.close()
            dingding_robo(self.web_server, self.site, 'error', self.username, self.phone_number)
            logs(self.username, self.ip, self.site, 'Failed')
            return 1




    def __iis_recycle(self,web_server,recycle_cmd,web_url,action):
        self.web_server = web_server
        self.recycle_cmd = recycle_cmd
        self.web_url = web_url
        self.action = action


        try:  ####recycle iis#######
            data = {
                'client': 'local',
                'tgt': self.web_server,
                'fun': 'cmd.run',
                'arg': self.recycle_cmd
            }

            print '----------',self.web_server,self.recycle_cmd
            recycle = salt_api.salt_cmd(data)
            print recycle
            if recycle['return'][0][self.web_server].find('successfully') < 0:
                print "!!!!!!!!!!!!!!!!!! [recycle iis] ERROR !!!!!!!!!!!!!!!!!!"
                return 1

            c = 5
            while c > 1:
                print c
                r = requests.get(self.web_url, headers={'Host': self.site}, timeout=60)
                c -= 1

            if self.action == 'recycle':
                dingding_robo(self.web_server, 'recycle ' + self.site, 'success', self.username, self.phone_number)
            elif self.action == 'revert':
                dingding_robo(self.web_server, 'revert ' + self.site, 'success', self.username, self.phone_number)
            else:
                dingding_robo(self.web_server,self.site, 'success', self.username, self.phone_number)
            return 0
        except Exception, e:
            print e
            self.f.write('error')
            self.f.close()
            if self.action == 'recycle':
                dingding_robo(self.web_server,self.site, 'error', self.username,self.phone_number)
            elif self.action == 'revert':
                dingding_robo(self.web_server,self.site, 'error', self.username,self.phone_number)
            else:
                dingding_robo(self.web_server,self.site, 'error', self.username,self.phone_number)
            logs(self.username, self.ip, self.site, 'Failed')
            return 1






    def deploy(self,site,action='svn',revision='HEAD',group=None):
        self.action = action
        self.revision = revision
        if group:
            obj = groupName.objects.get(group_name=group).member.values()
        else:
            obj = []
            obj.append({'webSite':site})
        for s in obj:
            self.site = s['webSite']
            info = webSite.objects.filter(env=self.env).get(webSite=self.site)
            ip = []
            for i in info.checkUrl.values(): ip.append(i['ip'])
            for host in info.checkUrl.values():
                print host['host'],info.webSite
                self.f.write('-----------------------%s---------------------\n' % info.webSite)
                self.f.flush()

                for m in info.state_module.values():
                    nginx_backup = self.__nginx_backup(ip,host['ip'],host['host'],m['state_module'],0)
                    if nginx_backup == 1:
                        self.f.write('Step 1: blocking nginx traffic is failed.\n')
                        exit()
                self.f.write('Step 1: blocking nginx traffic is sucessful.\n')
                self.f.flush()
                if self.action in ['svn','revert']:
                    svn_up = self.__svn_update(host['host'],info.svn_path,info.svn_username,info.svn_password,self.revision)
                    if svn_up == 1:
                        self.f.write('error')
                        exit()
                    else:
                        self.f.write('Step 2: svn update is sucessful.\n')
                        self.f.flush()
                elif self.action == 'recycle':
                    pass

                recycle = self.__iis_recycle(host['host'],info.recycle_cmd,host['url'],self.action)
                if recycle == 1:
                    self.f.write('error')
                    exit()
                elif action == 'recycle':
                    self.f.write('Step 2: iis recycle is sucessful.\n')
                    self.f.flush()
                else:
                    self.f.write('Step 3: iis recycle is sucessful.\n')
                    self.f.flush()


            for m in info.state_module.values():    ######nginx all online########
                status = self.__nginx_backup(ip,host['ip'],host['host'],m['state_module'],1)

                if status == 1:
                    logs(self.username, self.ip, self.site, 'Failed')
                    self.f.write('error')
                    exit()
            self.f.write('Last step: open nginx traffic is sucessful.\n')
            self.f.flush()
            logs(self.username, self.ip, self.site, 'Successful')
        self.f.write('done')
        self.f.flush()
        self.f.close()
        return self.result







@task
def deployWww(env,site,username,ip,fileName,phone_number):
    obj = wwwFun(env,username,ip,fileName,phone_number)
    obj.deploy(site,'svn')



@task
def deployWwwRecycle(env,site,username,ip,fileName,phone_number):
    obj = wwwFun(env,username,ip,fileName,phone_number)
    obj.deploy(site,'recycle')


@task
def deployWwwRevert(env,site,username,ip,fileName,reversion,phone_number):
    obj = wwwFun(env,username,ip,fileName,phone_number)
    obj.deploy(site,'revert',reversion)


@task
def deployWwwGroup(env,group_name,username,ip,fileName,phone_number):
    obj = wwwFun(env, username, ip, fileName, phone_number)
    obj.deploy(site=None, action='svn',revision='HEAD',group=group_name)

