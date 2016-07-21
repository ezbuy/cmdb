import os,time,commands,json
from salt.client import LocalClient
from www.models import *
from celery.task import task



@task
def deployWww(site):
    obj = webSite.objects.all()
    saltCmd = LocalClient()
    result = []
    data = {}
    f = open('/tmp/celery1.txt','w')
    for s in obj:
        if s.webSite == site:
            info = s
            break
    for host in info.checkUrl.values():
        print host['host']
        for m in info.state_module.values():
            print m['state_module']

            deploy_pillar = "pillar=\"{'deployserver':'" + host['host'] + "', 'deployhost':'" + info.salt_pillar_host + "'}\""
            print deploy_pillar
            try:
                s,backup = commands.getstatusoutput("salt " + info.lb_server + " state.sls " + m['state_module'] + " " + deploy_pillar)
                print '***************',backup

                f.write(backup)
                f.flush()
                f.write('\n\n\n\n\n')
                print '------*****************************backup11111---------'
            except Exception,e:
                print e
                exit()
                print '------backup---------'
        try:
            update_cmd = '\'svn update %s --username=deploy --password=ezbuyisthebest \'' % info.svn_path
            s,update = commands.getstatusoutput("salt " + host['host'] + " cmd.run " + update_cmd)
            f.write(update)
            f.flush()
            f.write('\n\n\n\n\n')
            print '------update1111---------'
        except Exception, e:
            print e
            print '------update---------'
            exit()



        ####recycle#######
        try:
            print '--------', info.recycle_cmd
            s, recycle = commands.getstatusoutput("salt " + host['host'] + " cmd.run '" + info.recycle_cmd + "'")
            f.write(recycle)
            f.flush()
            f.write('\n\n\n\n\n')

            print '------recycle---------'

            i = 0
            while i < 5:
                start_time = time.time()
                s,testUrl = commands.getstatusoutput("curl -H \"Host:" + site + "\" -I " + host['url'])
                f.write(testUrl)
                f.flush()
                f.write('\n\n\n\n\n')
                print time.time() - start_time
                if time.time() - start_time < 2:
                    break
                i = i + 1
            if i == 5:
                print "!!!!!!!!!!!!!!!!!! [recycle iis] TIMEOUT !!!!!!!!!!!!!!!!!!"
                exit()

        except Exception, e:
            print e
            exit()
            print '------recycle---------'

    ######none########
    for m in info.state_module.values():
        print m['state_module']
        deploy_pillar = "pillar=\"{'deployserver':'none', 'deployhost':'none'}\""
        try:
            s, none = commands.getstatusoutput(
                "salt " + info.lb_server + " state.sls " + m['state_module'] + " " + deploy_pillar)
            f.write(none)
            f.flush()
            print '------*****************************backup11111---------'
        except Exception, e:
            print e
            exit()
            print '------backup---------'


    f.write('\n\n\n\n\n')
    f.write('done')
    f.flush()
    f.close()

    return result