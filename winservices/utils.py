from winservices.models import winconf
from salt.client import LocalClient
from asset.utils import logs,notification





class servicesPublish:
    def __init__(self,user,ip):
        self.user = user
        self.ip = ip
        self.obj = winconf.objects.all()
        self.salt = LocalClient()


    def deployServices(self,env,services):
        self.env = env
        self.services = services
        result = []
        obj = winconf.objects.filter(env=self.env).filter(servicename=self.services)
        for name in obj:
            print name.servicename,name.hostname
            update_cmd = '\'svn update ' + name.localpath + '\''

            print update_cmd
            stop = self.salt.cmd(name.hostname.saltname,'cmd.run',['net stop %s' % name.servicename])
            result.append(stop)
            update = self.salt.cmd(name.hostname.saltname,'cmd.run',['%s' % update_cmd])
            result.append(update)
            start = self.salt.cmd(name.hostname.saltname,'cmd.run', ['net start %s' % name.servicename])
            result.append(start)

            action = 'deploy ' + name.servicename
            logs(self.user,self.ip,action,result)
            notification(name.hostname.saltname,name.servicename,start,self.user)



        return result



