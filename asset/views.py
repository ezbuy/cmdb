from django.shortcuts import render,render_to_response,HttpResponse
from django.contrib.auth.decorators import login_required
from asset.models import *
from asset.utils import *
from salt.client import LocalClient
import os,commands,re,json



@login_required
def asset_list(request):
    asset_list = Asset.objects.all()
    return render_to_response('jasset/asset_list.html',{'asset_list':asset_list})


@login_required
def get(request):
    groupname = gogroup.objects.all()
    return render_to_response('get.html',{'groupname':groupname})



@login_required
def getData(request):
    data = request.GET['goProject']
    env = request.GET['env']

    #if data == 'spike':
        #message = os.popen('ls /tmp')
        #a = 'sqlcmd -S 192.168.199.105 -U pengzihe -P pzh000 -d 2016 -Q "select * from class"'
        #message = sudo("salt t-slq-uat-testdb-1 cmd.run '%s'" % a)
    #host = ['test4']
    Publish = goPublish()
    result = Publish.deployGo(env, data)

    return render_to_response('getdata.html',{'result':result})
    #return HttpResponse(message)





@login_required
def goServices(request):

    data = request.GET.get('projectName')
    go = goServicesni(data)
    if data is not None:

        project = go.getServiceName()

    else:
        project = go.getServiceName()
    #return HttpResponse(project)
    return render_to_response('goservices.html',{'project':project})





@login_required
def getServices(request):
    data = request.GET.getlist('id')

    print data
    #host=['test4']
    #for i in host:
    for goName in data:
            for SN in goservices.objects.filter(name=goName):
                saltHost = str(SN.saltminion.saltname)

                message = "salt '%s' cmd.run 'supervisorctl restart %s'" % (saltHost,goName)
                os.system("echo %s >> /tmp/test.txt" % message)
                os.system("salt '%s' cmd.run 'supervisorctl restart %s' >> /tmp/test.txt" % (saltHost,goName))
    f = open('/tmp/test.txt', 'r')
    result = f.readlines()



    os.system('rm /tmp/test.txt')
    return render_to_response('getservices.html',{'result':result})


@login_required
def goRevert(request):
    groupname = gogroup.objects.all()

    tt = {'mico':12,'steven':23,'zero':110,'spike':'spike1111'}
    return render_to_response('gorevert.html',{'groupname':groupname,'tt':tt})


@login_required
def goRevertResult(request):
    data = request.GET['goProject']
    env = request.GET['env']
    print data
    print env
    #host = ['test4']
    Publish = goPublish()
    result = Publish.go_revert(env, data)
    return HttpResponse(result)

@login_required
def goRevertResulttwo(request):
    data = request.GET['goProject']
    env = request.GET['env']
    print env
    result = {}
    hostname = []
    value = 0

    revertFile = {}
    for obj in goservices.objects.filter(env=env):
        print type(obj.group.name)
        # for e in goservices.objects.filter(env=self.env):
        if obj.group.name == data:
            print obj.saltminion
            hostname.append(str(obj.saltminion.saltname))

    hostname = list(set(hostname))
    for h in hostname:
        fileName = commands.getstatusoutput('salt %s cmd.run "ls -t /tmp/%s | head -n 10"' % (h,data))[1].split()[1:]
        print fileName
        if 'no' in fileName:
            pass
        else:
            value=1
            revertFile[h]=fileName
        print revertFile
    if value == 1:
        result[env] = revertFile
    else:
        result = {}
    print result
    return render_to_response('gorevert2.html',{'fileName':result})



@login_required
def revert(request):

    if not request.GET.keys():

        return HttpResponse('mico!!')
    data = request.GET['id']
    #print '111111',data
    data = data.split(',')

    env = data[0]
    revertFile = data[1]

    #print env
    #print revertFile
    project = revertFile.split('_')[0]

    Publish = goPublish()
    result = Publish.go_revert(env,project,revertFile)

    return HttpResponse(result)