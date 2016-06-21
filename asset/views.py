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


    Publish = goPublish(env)
    result = Publish.deployGo(data)

    return render_to_response('getdata.html',{'result':result})






@login_required
def goServices(request):

    data = request.GET.get('projectName')
    go = goServicesni(data)
    groupName = gogroup.objects.all()
    #if data is not None:

    project = go.getServiceName()

    #else:
    #    project = go.getServiceName()

    return render_to_response('goservices.html',{'project':project,'groupName':groupName})





@login_required
def getServices(request):
    data = request.GET.getlist('id')
    print '222222221',data
    for v in data:
        goName,host = v.split(',')
        message = "salt '%s' cmd.run 'supervisorctl restart %s'" % (host,goName)
        os.system("echo %s >> /tmp/test.txt" % message)
        os.system("salt '%s' cmd.run 'supervisorctl restart %s' >> /tmp/test.txt" % (host,goName))
    f = open('/tmp/test.txt', 'r')
    result = f.readlines()
    f.close()



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

    Publish = goPublish(env)
    result = Publish.go_revert(data)
    return HttpResponse(result)

@login_required
def goRevertResulttwo(request):
    data = request.GET['goProject']
    env = request.GET['env']
    revertFile = {}
    result = {}
    hostname = []
    value = 0

    for obj in goservices.objects.filter(env=env):
        print type(obj.group.name)
        # for e in goservices.objects.filter(env=self.env):
        if obj.group.name == data:
            print obj.saltminion
            hostname.append(str(obj.saltminion.saltname))

    hostname = list(set(hostname))
    for h in hostname:
        fileName = commands.getstatusoutput('salt %s cmd.run "ls -t /tmp/%s | head -n 10"' % (h,data))[1].split()[1:]
        if 'no' in fileName or 'No' in fileName:
            pass
        else:
            value=1
            revertFile[h]=fileName

    if value == 1:
        result[env] = revertFile
    else:
        result = {}

    return render_to_response('gorevert2.html',{'fileName':result})



@login_required
def revert(request):

    if not request.GET.keys():
        mes = 'argv is error,not revert version!!'
        return render_to_response('goRevertResult.html', {'mes': mes})

    data = request.GET['id']
    data = data.split(',')
    env = data[0]
    revertFile = data[1]
    project = revertFile.split('_')[0]
    host = data[2]
    Publish = goPublish(env)
    mes = Publish.go_revert(project,revertFile,host)

    return render_to_response('goRevertResult.html',{'mes':mes})



@login_required
def goConfHTML(request):
    return render_to_response('goConf.html')


@login_required
def goConfResult(request):
    env = request.GET['env']
    Publish = goPublish(env)
    mes = Publish.goConf()
    return render_to_response('goConfResult.html',{'result':mes})