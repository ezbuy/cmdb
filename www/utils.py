import os,time,commands,json
from salt.client import LocalClient
from www.models import *
from celery.task import task



@task
def deployWww(env,site):

    obj = webSite.objects.filter(env=env).filter(webSite=site)
    saltCmd = LocalClient()
    result = []
    data = {}
    f = open('/tmp/celery1.txt','w')

    for info in obj:

        for host in info.checkUrl.values():
            print host['host']
            for m in info.state_module.values():

                try:   ##########nginx backup#######
                    deploy_pillar = "pillar=\"{'deployserver':'" + host['host'] + "', 'deployhost':'" + info.salt_pillar_host + "'}\""
                    s,backup = commands.getstatusoutput("salt " + info.lb_server + " state.sls " + m['state_module'] + " " + deploy_pillar)
                    f.write(backup)
                    f.flush()
                    f.write('\n\n\n\n\n')
                except Exception,e:
                    print e
                    f.write('error')
                    f.close()
                    exit()
            try:  #####svn update########
                update_cmd = '\'svn update %s --username=%s --password=%s \'' % (info.svn_path,info.svn_username,info.svn_password)
                s,update = commands.getstatusoutput("salt " + host['host'] + " cmd.run " + update_cmd)
                f.write(update)
                f.flush()
                f.write('\n\n\n\n\n')
            except Exception, e:
                print e
                f.write('error')
                f.close()
                exit()




            try:    ####recycle iis#######
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
                    f.write('error')
                    f.close()
                    exit()

            except Exception, e:
                print e
                f.write('error')
                f.close()
                exit()



        for m in info.state_module.values():    ######nginx all online########
            print m['state_module']
            deploy_pillar = "pillar=\"{'deployserver':'none', 'deployhost':'none'}\""
            try:
                s, none = commands.getstatusoutput("salt " + info.lb_server + " state.sls " + m['state_module'] + " " + deploy_pillar)
                f.write(none)
                f.flush()
            except Exception, e:
                print e
                f.write('error')
                f.close()
                exit()



    f.write('\n\n\n\n\n')
    f.write('done')
    f.flush()
    f.close()

    return result
