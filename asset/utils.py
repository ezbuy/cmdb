from asset.models import *

import os,time,commands

class goPublish:
    def __init__(self,host):
        self.host = host


    def getNowTime(self):
        return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(time.time()))



    def deployGo(self,env,name):
        self.env = env
        self.name = name
        if self.name == 'spike':
            projectServices = spike.objects.all()
        elif self.name == 'account':
            projectServices = account.objects.all()
        elif self.name == 'bulma':
            projectServices = bulma.objects.all()
        else:
            return "hi,i am mico!"

        Project = []
        for name in projectServices:
            if name.env == int(self.env):
                Project.append(name.name)

        line = '-' * 100
        os.system('echo "%s" >> /tmp/test.txt' % line)
        for i in self.host:
            deploy_pillar = "pillar=\"{'project':'" + self.name + "'}\""
            print deploy_pillar

            os.system("salt '%s' state.sls logs.gologs %s" % (i,deploy_pillar))
            currentTime = self.getNowTime()
            message = "salt %s cmd.run mv /srv/%s/%s /tmp/%s/%s_%s" %(i,self.name,self.name,self.name,self.name,currentTime)
            #print message
            os.system('echo "%s" >> /tmp/test.txt' % message)
            os.system("salt '%s' cmd.run 'mv /srv/%s/%s /tmp/%s/%s_%s && ls /tmp/%s' >> /tmp/test.txt" %(i,self.name,self.name,self.name,self.name,currentTime,self.name))
            message = "salt '%s' cmd.run 'svn update /srv/%s'" % (i,self.name)
            os.system("echo %s >> /tmp/test.txt" % message)
            os.system("salt '%s' cmd.run 'svn update --username=deploy --password=ezbuyisthebest --non-interactive /srv/%s' >> /tmp/test.txt" %(i,self.name))
            for s in Project:
                message ="salt '%s' cmd.run 'supervisorctl restart %s'" % (i,s)
                os.system("echo %s >> /tmp/test.txt" % message)
                os.system("salt '%s' cmd.run 'supervisorctl restart %s' >> /tmp/test.txt" % (i, s))

            #print line
            #revert = commands.getoutput("salt 'test4' cmd.run \"ls -lt /tmp | awk 'NR==2' | awk '{print \$NF}'\"")
            #print revert.split()[1]
            os.system('echo "%s" >> /tmp/test.txt' % line)
        f = open('/tmp/test.txt', 'r')
        result = f.readlines()

        #print result
        os.system('rm /tmp/test.txt')
        return result

    def go_revert(self,env,project):

        self.project = project

        projectPwd = "/srv/" + self.project + "/" + self.project
        currentTime = self.getNowTime()

        rename = "/tmp/revert/" + self.project + '_revert_' + currentTime
        runCmd = "'mv " + projectPwd + " " + rename + "'"

        for h in self.host:
            os.system("salt %s state.sls logs.revert" % h)
            os.system("salt '%s' cmd.run %s" %(h,runCmd))
            revertFile = commands.getoutput("salt '%s' cmd.run \'ls -lt /tmp/%s | awk \'NR==2\' | awk \"{print \$NF}\"\'" % (h,self.project))
            revertFile = revertFile.split()[-1]
            result = commands.getstatusoutput("salt '%s' cmd.run 'cp /tmp/%s/%s /srv/%s/%s'" %(h,self.project,revertFile,self.project,self.project))

        #print revertFile
        if result[0] == 0:
            print 'revert to last version is success.'

        return revertFile

class goServicesni:
    def __init__(self,projectName):
        self.projectName = projectName

    def spike(self):
        services = spike.objects.all()
        return services

    def account(self):
        accountServices = account.objects.all()
        return accountServices

    def bulma(self):
        bulmaServices = bulma.objects.all()
        return  bulmaServices




