from winservices.models import winconf
from salt.client import LocalClient
from asset.utils import logs,dingding_robo
import time




class servicesPublish:
    def __init__(self,user,ip):
        self.user = user
        self.ip = ip
        self.obj = winconf.objects.all()
        self.salt = LocalClient()


    def deployServices(self,env,services,phone_number):
        self.env = env
        self.services = services
        self.phone_number = phone_number
        result = []
        obj = winconf.objects.filter(env=self.env).filter(servicename=self.services)
        for name in obj:
            stop = self.salt.cmd(name.hostname.saltname,'cmd.run',['net stop %s' % name.servicename])
            result.append(stop)
            while True:
                task_list = self.salt.cmd(name.hostname.saltname, 'cmd.run', ['tasklist | findstr %s' % name.tasklist_name])
                if not task_list[name.hostname.saltname]:
                    print 'proccess has been exit.'
                    break
                time.sleep(3)
            update = self.salt.cmd(name.hostname.saltname,'cmd.run',['svn up %s --username=%s --password=%s' % (name.localpath,name.username,name.password)])
            result.append(update)
            start = self.salt.cmd(name.hostname.saltname,'cmd.run', ['net start %s' % name.servicename])
            result.append(start)

            action = 'deploy ' + name.servicename
            logs(self.user,self.ip,action,result)
            servicename = name.servicename.strip('"')
            dingding_robo(name.hostname.saltname,servicename,start,self.user,self.phone_number)

        return result


    def servicesAction(self,services,action,phone_number):
        self.services = services
        self.action = action
        self.phone_number = phone_number

        result = []

        for s in self.services:
            sName, host = s.split(',')
            if action == 'start':
                getMes = self.salt.cmd(host, 'cmd.run', ['net start %s' % sName])

            elif action == 'stop':
                getMes = self.salt.cmd(host, 'cmd.run', ['net stop %s' % sName])

            elif action == 'restart':
                getMes = self.salt.cmd(host, 'cmd.run', ['net stop %s' % sName])
                result.append(getMes)
                getMes = self.salt.cmd(host, 'cmd.run', ['net start %s' % sName])

            result.append(getMes)
            info = self.action + ' ' + sName.strip('"')
            dingding_robo(host, info, getMes, self.user,self.phone_number)
            logs(self.user, self.ip, info, result)

        return result
