from django.shortcuts import render,render_to_response,HttpResponse
from django.contrib.auth.decorators import login_required
from asset.models import *
from asset.utils import *
from salt.client import LocalClient
import os,commands,re



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
    name = 'spike'

    data = request.GET.get('projectName')
    go = goServicesni(data)
    #print data


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
    host=['test4']
    for i in host:
        for s in data:
            message = "salt '%s' cmd.run 'supervisorctl restart %s'" % (i, s)
            os.system("echo %s >> /tmp/test.txt" % message)
            os.system("salt '%s' cmd.run 'supervisorctl restart %s' >> /tmp/test.txt" % (i, s))
    f = open('/tmp/test.txt', 'r')
    result = f.readlines()



    os.system('rm /tmp/test.txt')
    return render_to_response('getservices.html',{'result':result})


@login_required
def goRevert(request):
    groupname = gogroup.objects.all()
    return render_to_response('gorevert.html',{'groupname':groupname})


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