
from django.shortcuts import render,render_to_response,HttpResponse,HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from asset.models import *
from asset.utils import *
from salt.client import LocalClient
import os,commands,re,json
from asset.utils import getNowTime,get_cronjob_list
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger





@login_required
def asset_list(request):
    asset_list = Asset.objects.all().order_by('hostname')
    return render(request,'asset/asset_list.html',{'asset_list':asset_list})


@login_required
@deny_resubmit(page_key='deploy_go')
def get(request):
    groupname = gogroup.objects.all()
    return render(request,'get.html',{'groupname':groupname})



@login_required
@deny_resubmit(page_key='deploy_go')
def getData(request):
    if not request.POST.keys():
        return HttpResponseRedirect('/')
    data = request.POST['goProject']
    env = request.POST['env']
    services = request.POST.getlist('services', [])
    tower_url = request.POST['url']
    ip = request.META['REMOTE_ADDR']
    Publish = goPublish(env)

    result = []
    for svc in services:
        rst = Publish.deployGo(data, svc, request.user, ip, tower_url, request.POST['phone_number'])
        result.extend(rst)

        # break once deploy failed
        if not get_service_status(svc):
            print("deploy %s failed" % svc)
            break

    return render(request,'getdata.html',{'result':result})






@login_required
@deny_resubmit(page_key='go_method')
def goServices(request):
    project_name = request.GET.get('projectName')
    go = goServicesni(project_name)
    group_name = gogroup.objects.all()
    services_list = go.getServiceName()
    paginator = Paginator(services_list, 20)
    page = request.GET.get('page')

    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        contacts = paginator.page(1)
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)

    return render(request,'goservices.html',{'project':contacts,'groupName':group_name,'project_name':project_name})





@login_required
@deny_resubmit(page_key='go_method')
def getServices(request):
    action = request.POST.get('action')
    data = request.POST.getlist('id')
    username = request.user
    saltCmd = LocalClient()
    result = []
    ip = request.META['REMOTE_ADDR']

    for v in data:
        goName,host = v.split(',')
        getMes = saltCmd.cmd('%s'%host,'cmd.run',['supervisorctl %s %s'% (action,goName)])
        result.append(getMes)
        info = action + ' ' + goName
        dingding_robo(host,info,getMes,username,request.POST['phone_number'])
    logs(username,ip,'%s services' % action,result)


    return render(request,'getdata.html',{'result':result})


@login_required
@deny_resubmit(page_key='revert_go')
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
def get_go_revert_list(request):
    env = request.POST['env']
    project = request.POST['project']
    services = request.POST['services']
    info = GoServiceRevision.objects.filter(name=project).order_by('-id')[0:20]
    return render(request,'get_go_revert_list.html',{'info':info, 'env':env, 'services': services})

@login_required
@deny_resubmit(page_key='revert_go')
def revert(request):
    if not request.POST.getlist('info'):
        mes = [{'Error':'Not rollback version number!!'}]
        return render(request,'getdata.html', {'result': mes})

    info = request.POST['info']
    print info

    info = info.split(',')
    project = info[0]
    go_reversion = info[1]
    gotemplate_revision = info[2]
    service = info[3]
    env = info[4]
    ip = request.META['REMOTE_ADDR']
    tower_url = 'http://tower.im'

    Publish = goPublish(env)
    mes = Publish.deployGo(project,service,request.user,ip,tower_url,request.POST['phone_number'],go_reversion,gotemplate_revision)
    return render(request, 'getdata.html', {'result': mes})




@login_required
@deny_resubmit(page_key='deploy_goconf')
def goConfHTML(request):
    return render(request,'goConf.html')


@login_required
@deny_resubmit(page_key='deploy_goconf')
def goConfResult(request):
    env = request.POST['env']
    project = request.POST['project']
    ip = request.META['REMOTE_ADDR']
    username = request.user
    phone_number = request.POST['phone_number']
    Publish = goPublish(env)
    mes = Publish.goConf(project,username,ip,phone_number)
    return render(request,'getdata.html',{'result':mes})

@login_required
def test(request):
    syncAsset()
    return HttpResponseRedirect('/asset/list')

@login_required
def qcloud(request):
    syncQcloud()
    return HttpResponseRedirect('/asset/list')

@login_required
def qingcloud(request):
    syncQingcloud()
    return HttpResponseRedirect('/asset/list')

@login_required
@deny_resubmit(page_key='deploy_go')
def getProjectList(request):
    project = request.GET['project']
    env = request.GET['env']
    result = []
    go = goservices.objects.filter(env=env).filter(group_id__name=project)
    for name in go:
        result.append(name.name)

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
    username = request.user
    ip = request.META['REMOTE_ADDR']
    env = request.GET['env']
    hostname = request.GET['hostname']
    project = request.GET['project']
    supervisorName = request.GET['supervisorname']
    goCommand = request.GET['command']
    svnRepo = request.GET['svnrepo']
    svnUsername = request.GET['svnusername']
    svnPassword = request.GET['svnpassword']
    fileName = '/tmp/build_go_' + getNowTime()


    deploy = deploy_go.delay(env,hostname,project,supervisorName,goCommand,svnRepo,svnUsername,svnPassword,fileName,username,ip)

    if deploy.id:
        return render(request,'getText.html',{'fileName':fileName})
    else:
        return HttpResponse('celery error!')




@login_required
def go_status(request):
    hostname_id = request.POST.get('hostname')
    obj = go_monitor_status()
    hosts = obj.get_hosts()

    if hostname_id is not None:
        status = obj.get_supervisor_status(hostname_id)
        return render(request, 'gostatus.html', {'hosts': hosts, 'status': status})
    else:
        return render(request, 'gostatus.html', {'hosts': hosts})


@login_required
@deny_resubmit(page_key='project_crontab')
def crontab_update(request):
    login_user = request.user
    ip = request.META['REMOTE_ADDR']
    obj = crontab_svn_status(login_user,ip)
    status = obj.get_crontab_list()


    if not request.POST.keys():
        return render(request, 'crontabupdate.html', {'status': status})
    else:
        data = request.POST['project']
        data = data.split("::")
        project = data[0]
        hostname = data[1]
        result = obj.crontab_svn_update(hostname,project,request.POST['phone_number'])
        return render(request,'getdata.html',{'result':result})

@login_required
def cronjob_list(request):
    cron_list = get_cronjob_list()
    paginator = Paginator(cron_list, 20)
    page = request.GET.get('page')

    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        contacts = paginator.page(1)
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)
    return render(request,'cronjob_list.html',{'cron_list':contacts})


@login_required
@deny_resubmit(page_key='go_template')
def go_template_html(request):
    return render(request,'go_template.html')

@login_required
@deny_resubmit(page_key='go_template')
def get_gotemplate_project(request):
    go_template = GOTemplate.objects.all()
    env = request.GET['env']
    project = []
    for i in go_template:
        if str(i.env) == env:
            project.append(i.project.name)

    project = list(set(project))

    return HttpResponse(json.dumps(project))

@login_required
@deny_resubmit(page_key='go_template')
def go_template_result(request):
    env = request.POST['env']
    project = request.POST['project']
    ip = request.META['REMOTE_ADDR']
    username = request.user
    Publish = goPublish(env)
    mes = Publish.go_template(project,username,ip,request.POST['phone_number'])
    return render(request,'getdata.html',{'result':mes})
