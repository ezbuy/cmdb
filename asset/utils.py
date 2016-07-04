from asset.models import *
from asset import models
import os,time,commands
from salt.client import LocalClient
from logs.models import goLog

def notification(hostname, project, result, username):

    if result.values()[0].find('ERROR') > 0 or result.values()[0].find('error') > 0 or result.values()[0].find('Skip') > 0:
        errmsg = 'Failed'
    else:
        errmsg = 'Success'

    notificaction = 'curl -X POST -H \'Content-Type:application/json;\' -d \'{"hostname":"%s by %s", "ip":"null", "project":"%s", "gitcommit":"null", "gitmsg":"null", "errmsg":"%s","errcode":true}\' http://dlog.65dg.me/dlog' % (
        hostname, username, project, errmsg)


    #print '-------', notificaction
    apiResult = os.system(notificaction)
    return apiResult


def logs(user,ip,action,result):
    goLog.objects.create(user=user, remote_ip=ip, goAction=action, result=result)


class goPublish:
    def __init__(self,env):
        self.env = env
        self.saltCmd = LocalClient()
        self.svnInfo = models.svn.objects.all()


    def getNowTime(self):
        return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(time.time()))


    def deployGo(self,name,services,username,ip):

        self.name = name
        self.services = services
        self.username = username
        self.ip = ip
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
                        if self.services == 'all':
                            golist = [obj.name]
                            if hostInfo.has_key(saltHost):
                                services.append(obj.name)
                            else:
                                services = golist
                                hostInfo[saltHost] = services
                        else:
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


            ding = notification(host,self.name,restart,self.username)


        action = 'deploy ' + self.name
        logs(self.username,self.ip,action,result)


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
                ding = notification(self.host,info,mes,username)

                result.append(mes)

        action = 'revert ' + self.project
        logs(self.username, self.ip, action, result)
        return result


    def goConf(self,project,usernmae,ip):
        self.project = project
        self.username = usernmae
        self.ip = ip
        result = []
        conf = goconf.objects.all()



        for p in conf:

            if str(p.env) == self.env and p.project.name == self.project:
                #print p.username,p.password,p.localpath,p.hostname
                confCmd = "svn update --username=%s --password=%s --non-interactive %s" %(p.username,p.password,p.localpath)
                confResult = self.saltCmd.cmd('%s' % p.hostname,'cmd.run',['%s' % confCmd])
                result.append(confResult)

                info = self.project + ' conf'


                ding = notification(p.hostname,self.project,confResult,self.username)

        action = 'conf ' + self.project
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




