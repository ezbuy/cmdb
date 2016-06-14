from django.shortcuts import render,render_to_response,HttpResponse
from asset.models import *
from asset.utils import *


from salt.client import LocalClient




import os,commands,re
def asset_list(request):
    asset_list = Asset.objects.all()
    return render_to_response('jasset/asset_list.html',{'asset_list':asset_list})



def get(request):
    return render_to_response('get.html')




def getData(request):
    data = request.GET['goProject']
    env = request.GET['env']

    #if data == 'spike':
        #message = os.popen('ls /tmp')
        #a = 'sqlcmd -S 192.168.199.105 -U pengzihe -P pzh000 -d 2016 -Q "select * from class"'
        #message = sudo("salt t-slq-uat-testdb-1 cmd.run '%s'" % a)
    host = ['test4']
    Publish = goPublish(host)
    result = Publish.deployGo(env, data)
    #print Publish.go_revert('spike')
    print result
    #else:
    #    return HttpResponse('No services!!')
    return render_to_response('getdata.html',{'result':result})
    #return HttpResponse(message)






def goServices(request):
    name = 'spike'
    go = goServicesni(name)
    data = request.GET.get('projectName')
    print data


    if data is not None:
        if data =="spike":
            project = go.spike()
        elif data == "account":
            project = go.account()
        elif data == "bulma":
            project = go.bulma()
        else:
            return HttpResponse("i am mico!")
    else:
        project = go.spike()
    #return HttpResponse(project)
    return render_to_response('goservices.html',{'project':project})






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
    #return HttpResponse(data)


    os.system('rm /tmp/test.txt')
    return render_to_response('getservices.html',{'result':result})


def goRevert(request):
    return render_to_response('gorevert.html')


def goRevertResult(request):
    data = request.GET['goProject']
    env = request.GET['env']
    host = ['test4']
    Publish = goPublish(host)
    result = Publish.go_revert(env, data)
    return HttpResponse(result)