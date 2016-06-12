from asset.models import *
import os,time,commands

class goPublish:
    def __init__(self,host):
        self.host = host


    def getNowTime(self):
        return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(time.time()))



    def spike(self):
        spikeServices = spike.objects.all()
        line = '-' * 100
        os.system('echo "%s" >> /tmp/test.txt' % line)
        for i in self.host:
            currentTime = self.getNowTime()
            message = "salt %s cmd.run mv /srv/spike/spike /tmp/spike_%s" %(i,currentTime)
            #print message
            os.system('echo "%s" >> /tmp/test.txt' % message)
            os.system("salt '%s' cmd.run 'mv /srv/spike/spike /tmp/spike_%s && ls /tmp' >> /tmp/test.txt" %(i,currentTime))
            message = "salt '%s' cmd.run 'svn update /srv/spike'" % (i)
            os.system("echo %s >> /tmp/test.txt" % message)
            os.system("salt '%s' cmd.run 'svn update --username=deploy --password=ezbuyisthebest --non-interactive /srv/spike' >> /tmp/test.txt" % i)
            for s in spikeServices:
                message ="salt '%s' cmd.run 'supervisorctl restart %s'" % (i,s)
                os.system("echo %s >> /tmp/test.txt" % message)
                os.system("salt '%s' cmd.run 'supervisorctl restart %s' >> /tmp/test.txt" % (i, s))

            #print line
            revert = commands.getoutput("salt 'test4' cmd.run \"ls -lt /tmp | awk 'NR==2' | awk '{print \$NF}'\"")
            print revert.split()[1]
            os.system('echo "%s" >> /tmp/test.txt' % line)
        f = open('/tmp/test.txt', 'r')
        result = f.readlines()

        #print result
        os.system('rm /tmp/test.txt')
        return result

class goServicesni:
    def __init__(self,projectName):
        self.projectName = projectName

    def spike(self):
        a = self.projectName
        print '------------',a
        services = spike.objects.all()
        #print services
        return services

    def account(self):
        accountServices = account.objects.all()
        return accountServices