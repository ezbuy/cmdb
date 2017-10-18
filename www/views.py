from django.shortcuts import render,render_to_response,HttpResponse
from django.contrib.auth.decorators import login_required

# Create your views here.
from www.utils import deployWww,deployWwwRecycle,deployWwwRevert,deployWwwGroup
from www.models import webSite,groupName
from asset.utils import getNowTime,deny_resubmit
import json




@login_required
@deny_resubmit(page_key='deploy_iis')
def wwwList(request):
    return render(request,'wwwList.html')


@login_required
@deny_resubmit(page_key='deploy_revert')
def wwwRevertList(request):
    return render(request,'wwwRevertList.html')

@login_required
def getProjectName(request):
    env = request.GET['env']
    obj = webSite.objects.filter(env=env)
    servicesList = []
    for name in obj:
        servicesList.append(name.webSite)

    return  HttpResponse(json.dumps(servicesList))

@login_required
@deny_resubmit(page_key='deploy_iis')
def deployIis(request):
     env = request.POST['env']
     site = request.POST['project']
     username = request.user
     ip = request.META['REMOTE_ADDR']
     fileName = '/tmp/deployIis_' + getNowTime()
     deploy = deployWww.delay(env,site,username,ip,fileName,request.POST['phone_number'])
     if deploy.id:
        return render(request,'getText.html',{'fileName':fileName})
     else:
        return HttpResponse('celery error!')


@login_required
@deny_resubmit(page_key='deploy_recycle')
def recycleList(request):
    if 'env' in request.GET:
        env = request.GET['env']
    else:
        env = 1
    site = webSite.objects.filter(env=int(env))
    return render(request,'recyclelist.html', {'project': site})


@login_required
@deny_resubmit(page_key='deploy_recycle')
def deployRecycle(request):
    data = request.POST.getlist('id')
    site,env = data[0].split(',')
    username = request.user
    ip = request.META['REMOTE_ADDR']
    fileName = '/tmp/deployRecycle_' + getNowTime()
    deploy = deployWwwRecycle.delay(env,site,username,ip,fileName,request.POST['phone_number'])
    if deploy.id:
        return render(request,'getText.html',{'fileName':fileName})
    else:
        return HttpResponse('celery error!')


@login_required
@deny_resubmit(page_key='deploy_revert')
def deployRevertIis(request):
     env = request.POST['env']
     site = request.POST['project']
     revision = request.POST['svnRevision']
     username = request.user
     ip = request.META['REMOTE_ADDR']
     fileName = '/tmp/deployRevertIis_' + getNowTime()

     if int(revision) == 1:
         revision = 'PREV'

     deploy = deployWwwRevert.delay(env,site,username,ip,fileName,revision,request.POST['phone_number'])
     if deploy.id:
        return render(request,'getText.html',{'fileName':fileName})
     else:
        return HttpResponse('celery error!')

@login_required
@deny_resubmit(page_key='deploy_group')
def getGroup(request):
    group = groupName.objects.all()
    return  render(request,'wwwGroup.html', {'group': group})


@login_required
@deny_resubmit(page_key='deploy_group')
def deployGroup(request):
     env = '1'
     group = request.POST['group_name']
     print '----group----',group
     username = request.user
     ip = request.META['REMOTE_ADDR']
     fileName = '/tmp/deployGroup_' + getNowTime()
     deploy = deployWwwGroup.delay(env,group,username,ip,fileName,request.POST['phone_number'])
     if deploy.id:
        return render(request,'getText.html',{'fileName':fileName})
     else:
        return HttpResponse('celery error!')

