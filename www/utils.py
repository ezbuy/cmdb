import os,time,commands,json
from salt.client import LocalClient
from www.models import *
from celery.task import task
from asset.utils import notification,logs






class wwwFun:
    def __init__(self,env,username,ip):
        self.env = env
        self.username = username
        self.ip = ip
        self.f = open('/tmp/celery1.txt','w')




    def __nginx_backup(self,proxy_server,web_server,nginx_module,deploy_pillar):
        self.proxy_server = proxy_server
        self.web_server = web_server
        self.nginx_module = nginx_module
        self.deploy_pillar = deploy_pillar

        try:  ##########nginx backup#######

            s, backup = commands.getstatusoutput("salt " + self.proxy_server + " state.sls " + self.nginx_module + " " + self.deploy_pillar)
            self.f.write(backup)
            self.f.flush()
            self.f.write('\n\n\n\n\n')
            return 0
        except Exception, e:
            print e
            self.f.write('error')
            self.f.close()
            notification(self.web_server, self.site, 'error', self.username)
            logs(self.username, self.ip, self.site, 'Failed')
            exit()




    def __svn_update(self,web_server,svn_path,svn_username,svn_password):
        self.web_server = web_server
        self.svn_path = svn_path
        self.svn_username = svn_username
        self.svn_password = svn_password



        try:  #####svn update########
            update_cmd = '\'svn update %s --username=%s --password=%s \'' % (self.svn_path, self.svn_username, self.svn_password)
            s, update = commands.getstatusoutput("salt " + self.web_server + " cmd.run " + update_cmd)
            self.f.write(update)
            self.f.flush()
            self.f.write('\n\n\n\n\n')
        except Exception, e:
            print e
            self.f.write('error')
            self.f.close()
            notification(self.web_server, self.site, 'error', self.username)
            logs(self.username, self.ip, self.site, 'Failed')
            exit()


    def __iis_recycle(self,web_server,recycle_cmd,web_url):
        self.web_server = web_server
        self.recycle_cmd = recycle_cmd
        self.web_url = web_url


        try:  ####recycle iis#######
            s, recycle = commands.getstatusoutput("salt " + self.web_server + " cmd.run '" + self.recycle_cmd + "'")
            self.f.write(recycle)
            self.f.flush()
            self.f.write('\n\n\n\n\n')

            print '------recycle---------'

            i = 0
            while i < 5:
                start_time = time.time()
                s, testUrl = commands.getstatusoutput("curl -H \"Host:" + self.site + "\" -I " + self.web_url)
                self.f.write(testUrl)
                self.f.flush()
                self.f.write('\n\n\n\n\n')
                print time.time() - start_time
                if time.time() - start_time < 2:
                    break
                i = i + 1
            if i == 5:
                print "!!!!!!!!!!!!!!!!!! [recycle iis] TIMEOUT !!!!!!!!!!!!!!!!!!"
                self.f.write('error')
                self.f.close()
                exit()

            notification(self.web_server, self.site, 'success', self.username)

        except Exception, e:
            print e
            self.f.write('error')
            self.f.close()
            notification(self.web_server, self.site, 'error', self.username)
            logs(self.username, self.ip, self.site, 'Failed')
            exit()






    def deploy(self,site,action='svn'):

        self.site = site
        self.action = action
        obj = webSite.objects.filter(env=self.env).filter(webSite=self.site)



        for info in obj:
            for host in info.checkUrl.values():
                print host['host']
                for m in info.state_module.values():
                    deploy_pillar = "pillar=\"{'deployserver':'" + host['host'] + "', 'deployhost':'" + info.salt_pillar_host + "'}\""
                    self.__nginx_backup(info.lb_server,host['host'],m['state_module'],deploy_pillar)
                if self.action == 'svn':
                    self.__svn_update(host['host'],info.svn_path,info.svn_username,info.svn_password)
                elif self.action == 'recycle':
                    pass
                self.__iis_recycle(host['host'],info.recycle_cmd,host['url'])
            for m in info.state_module.values():    ######nginx all online########
                print m['state_module']
                deploy_pillar = "pillar=\"{'deployserver':'none', 'deployhost':'none'}\""
                status = self.__nginx_backup(info.lb_server,host['host'],m['state_module'],deploy_pillar)

        if status != 0:
            logs(self.username, self.ip, self.site, 'Failed')
            return 'Failed'
        self.f.write('done')
        self.f.flush()
        self.f.close()
        logs(self.username, self.ip, self.site, 'Successful')
        return 'Successful'







@task
def deployWww(env,site,username,ip):
    obj = wwwFun(env,username,ip)
    obj.deploy(site,'svn')



@task
def deployWwwRecycle(env,site,username,ip):
    obj = wwwFun(env,username,ip)
    obj.deploy(site,'recycle')
