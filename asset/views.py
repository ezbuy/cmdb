from django.shortcuts import render,render_to_response,HttpResponse
from asset.models import *
from asset.utils import *


from salt.client import LocalClient


from fabric.api import (
    env,
    hosts,
    execute,
    run,
    settings,
    sudo,
    task,
)


import os,commands,re
def asset_list(request):
    asset_list = Asset.objects.all()
    return render_to_response('jasset/asset_list.html',{'asset_list':asset_list})

def get(request):
    return render_to_response('get.html')

def getData(request):
    data = request.GET['username']

    if data == 'spike':
        #message = os.popen('ls /tmp')
        #a = 'sqlcmd -S 192.168.199.105 -U pengzihe -P pzh000 -d 2016 -Q "select * from class"'
        #message = sudo("salt t-slq-uat-testdb-1 cmd.run '%s'" % a)
        host = ['test4']
        spikePublish = goPublish(host)
        result = spikePublish.spike()
        print result
    return render_to_response('getdata.html',{'result':result})
    #return HttpResponse(message)

def goServices(request):
    name = 'spike'
    go = goServicesni(name)
    spikeProject = go.spike()
    accountProject = go.account()
    #return HttpResponse(project)
    return render_to_response('goservices.html',{'spikeProject':spikeProject,'accountProject':accountProject})