
from django.shortcuts import render,render_to_response,HttpResponse
from django.contrib.auth.decorators import login_required
from asset.models import *
from asset.utils import *
from salt.client import LocalClient
import os,commands,re,json
from asset.utils import getNowTime


@login_required
def asset_list(request):
    asset_list = Asset.objects.all()
    return render(request,'asset/asset_list.html',{'asset_list':asset_list})


@login_required
def get(request):
    groupname = gogroup.objects.all()


    return render(request,'get.html',{'groupname':groupname})



@login_required
def getData(request):
    data = request.GET['goProject']
    env = request.GET['env']
    services = request.GET['services']
    username = request.user
    ip = request.META['REMOTE_ADDR']
    Publish = goPublish(env)
    result = Publish.deployGo(data,services,username,ip)


    return render(request,'getdata.html',{'result':result})






@login_required
def goServices(request):

    data = request.GET.get('projectName')
    go = goServicesni(data)
    groupName = gogroup.objects.all()
    project = go.getServiceName()

    return render(request,'goservices.html',{'project':project,'groupName':groupName})





@login_required
def getServices(request):
    data = request.GET.getlist('id')
    username = request.user
    saltCmd = LocalClient()
    result = []
    ip = request.META['REMOTE_ADDR']


    for v in data:
        goName,host = v.split(',')
        getMes = saltCmd.cmd('%s'%host,'cmd.run',['supervisorctl restart %s'%goName])
        result.append(getMes)
        info = 'restart ' + goName
        notification(host,info,getMes,username)
    logs(username,ip,'restart services',result)


    return render(request,'getdata.html',{'result':result})


@login_required
def goRevert(request):
    groupname = gogroup.objects.all()


    return render(request,'gorevert.html',{'groupname':groupname})


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
        if obj.group.name == data:
            hostname.append(str(obj.saltminion.saltname))

    hostname = list(set(hostname))
    for h in hostname:
        fileName = commands.getstatusoutput('salt %s cmd.run "ls -t /tmp/%s | head -n 10"' % (h,data))[1].split()[1:]
        if 'no' in fileName or 'No' in fileName or 'not' in fileName or 'Not' in fileName:   #minion is offline
            pass
        else:
            value=1
            revertFile[h]=fileName

    if value == 1:
        result[env] = revertFile
    else:
        result = {}

    return render(request,'gorevert2.html',{'fileName':result})



@login_required
def revert(request):

    if not request.GET.keys():
        mes = 'argv is error,not revert version!!'
        return render(request,'goRevertResult.html', {'mes': mes})

    data = request.GET['id']
    username = request.user
    ip = request.META['REMOTE_ADDR']
    data = data.split(',')
    env = data[0]
    revertFile = data[1]
    project = revertFile.split('_')[0]
    host = data[2]
    Publish = goPublish(env)
    mes = Publish.go_revert(project,revertFile,host,username,ip)

    return render(request,'getdata.html',{'result':mes})



@login_required
def goConfHTML(request):
    return render(request,'goConf.html')


@login_required
def goConfResult(request):
    env = request.GET['env']
    project = request.GET['project']
    ip = request.META['REMOTE_ADDR']
    username = request.user
    Publish = goPublish(env)
    mes = Publish.goConf(project,username,ip)
    return render(request,'getdata.html',{'result':mes})


def test(request):
    syncAsset()
    return render(request,'test.html')

@login_required
def getProjectList(request):
    project = request.GET['project']
    env = request.GET['env']
    result = []
    go = goservices.objects.filter(env=env).filter(group_id__name=project)
    for name in go:
        result.append(name.name)
    if result:
        result.append('all')
    result = list(set(result))

    return HttpResponse(json.dumps(result))

@login_required
def getBuildList(request):
    env = request.GET['env']
    host = gobuild.objects.filter(env=env)
    result = []
    for h in host:
        result.append(str(h.hostname))
    return HttpResponse(json.dumps(result))


@login_required
def getConfProject(request):
    conf = goconf.objects.all()
    env = request.GET['env']
    project = []
    for i in conf:
        if str(i.env) == env:
            project.append(i.project.name)

    project = list(set(project))

    return HttpResponse(json.dumps(project))

@login_required
def getText(request):
    fileName = request.GET['fileName']

    if os.path.exists(fileName):
        f = open(fileName, 'r')
        info = f.read()
        s, end = commands.getstatusoutput('tail -n 1 %s' % fileName)
        if end == 'done' or end == 'error':
            commands.getstatusoutput('rm %s' % fileName)
    else:
        info = ''
        end = ''
    content = {'info': info, 'end': end}
    return HttpResponse(json.dumps(content))


@login_required
def go_build(request):
    return render(request,'gobuild.html')


@login_required
def build_go(request):
    env = request.GET['env']
    hostname = request.GET['hostname']
    project = request.GET['project']
    supervisorName = request.GET['supervisorname']
    goCommand = request.GET['command']
    svnRepo = request.GET['svnrepo']
    svnUsername = request.GET['svnusername']
    svnPassword = request.GET['svnpassword']
    fileName = '/tmp/build_go_' + getNowTime()


    deploy = deploy_go.delay(env,hostname,project,supervisorName,goCommand,svnRepo,svnUsername,svnPassword,fileName)

    if deploy.id:
        return render(request,'getText.html',{'fileName':fileName})
    else:
        return HttpResponse('celery error!')


