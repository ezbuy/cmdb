from asset.models import *

import os,time,commands

class goPublish:
    def __init__(self,env):
        self.env = env


    def getNowTime(self):
        return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(time.time()))



    def deployGo(self,name):

        self.name = name
        Project = []
        salt = []
        saltcount = 0
        line = '-' * 100
        os.system('echo "%s" >> /tmp/test.txt' % line)
        minionHost = commands.getstatusoutput('salt-key -l accepted')[1].split()[2:]
        print minionHost
        groupname = gogroup.objects.all()
        for name in groupname:
            if self.name == name.name:
                for obj in goservices.objects.filter(env=self.env).filter(group_id=name.id):
                    Project.append(obj)

                    for saltname in minion.objects.filter(id=obj.saltminion_id):

                        i = saltname.saltname
                        if i not in salt:
                            salt.append(i)
                            saltcount = 1
                        else:
                            saltcount = 0

                        if i not in minionHost:
                            print 'No minions matched the %s host.' % i
                            os.system('echo "No minions matched the %s host,please check your configure." >> /tmp/test.txt' % i)
                        else:
                            if saltcount == 1:


                                deploy_pillar = "pillar=\"{'project':'" + self.name + "'}\""
                                print deploy_pillar

                                os.system("salt '%s' state.sls logs.gologs %s" % (i,deploy_pillar))
                                currentTime = self.getNowTime()
                                message = "salt %s cmd.run mv /srv/%s/%s /tmp/%s/%s_%s" %(i,self.name,self.name,self.name,self.name,currentTime)
                                os.system('echo "%s" >> /tmp/test.txt' % message)
                                os.system("salt '%s' cmd.run 'mv /srv/%s/%s /tmp/%s/%s_%s && ls /tmp/%s' >> /tmp/test.txt" %(i,self.name,self.name,self.name,self.name,currentTime,self.name))
                                message = "salt '%s' cmd.run 'svn update /srv/%s'" % (i,self.name)
                                os.system("echo %s >> /tmp/test.txt" % message)
                                os.system("salt '%s' cmd.run 'svn update --username=deploy --password=ezbuyisthebest --non-interactive /srv/%s' >> /tmp/test.txt" %(i,self.name))

                            message ="salt '%s' cmd.run 'supervisorctl restart %s'" % (i,obj)
                            os.system("echo %s >> /tmp/test.txt" % message)
                            os.system("salt '%s' cmd.run 'supervisorctl restart %s' >> /tmp/test.txt" % (i, obj))


        os.system('echo "%s" >> /tmp/test.txt' % line)
        f = open('/tmp/test.txt', 'r')
        result = f.readlines()
        f.close()


        os.system('rm /tmp/test.txt')
        return result

    def go_revert(self,project,revertFile,host):

        self.project = project
        self.revertFile = revertFile
        self.host = host
        projectPwd = "/srv/" + self.project + "/" + self.project
        currentTime = self.getNowTime()

        rename = "/tmp/revert/" + self.project + '_revert_' + currentTime
        runCmd = "'mv " + projectPwd + " " + rename + "'"

        os.system("salt %s state.sls logs.revert" % self.host)
        os.system("salt '%s' cmd.run %s" %(self.host,runCmd))
        revertResult = commands.getstatusoutput("salt '%s' cmd.run 'cp /tmp/%s/%s /srv/%s/%s'" %(self.host,self.project,self.revertFile,self.project,self.project))
        for obj in goservices.objects.filter(env=self.env):
                if obj.group.name == self.project and self.host == obj.saltminion.saltname:
                    os.system("salt %s cmd.run 'supervisorctl restart %s'"%(self.host,obj.name))

        if revertResult[0] == 0:
            mes = 'revert to %s version is successful.' % revertFile
        else:
            mes = 'revert to %s version is failed.' % revertFile

        return mes


    def goConf(self):
        hostname = []
        if self.env == '1' or self.env == '2':
            for obj in goservices.objects.filter(env=self.env):
                hostname.append(str(obj.saltminion.saltname))
        hostname = list(set(hostname))
        confCmd = "svn update --username=deploy --password=ezbuyisthebest --non-interactive /srv/goconf"
        for h in hostname:
            confResult =  os.system('salt %s cmd.run "%s" >> /tmp/goconf.txt' %(h,confCmd))

        f = file('/tmp/goconf.txt','r')
        result = f.readlines()
        f.close()
        os.system('rm /tmp/goconf.txt')
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




