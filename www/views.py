from django.shortcuts import render,render_to_response,HttpResponse
from django.contrib.auth.decorators import login_required

# Create your views here.
from www.utils import deployWww,deployWwwRecycle
from www.models import webSite
from asset.utils import getNowTime
import json




@login_required
def wwwList(request):
    return render_to_response('wwwList.html')



@login_required
def getProjectName(request):
    env = request.GET['env']
    obj = webSite.objects.filter(env=env)
    servicesList = []
    for name in obj:
        servicesList.append(name.webSite)

    return  HttpResponse(json.dumps(servicesList))

@login_required
def deployIis(request):
     env = request.GET['env']
     site = request.GET['project']
     username = request.user
     ip = request.META['REMOTE_ADDR']
     fileName = '/tmp/deployIis_' + getNowTime()
     deploy = deployWww.delay(env,site,username,ip,fileName)
     if deploy.id:
        return render_to_response('getText.html')
     else:
        return HttpResponse('celery error!')


@login_required
def recycleList(request):
    if 'env' in request.GET:
        env = request.GET['env']
    else:
        env = 1
    site = webSite.objects.filter(env=int(env))
    return render_to_response('recyclelist.html', {'project': site})


@login_required
def deployRecycle(request):
    data = request.GET.getlist('id')
    site,env = data[0].split(',')
    username = request.user
    ip = request.META['REMOTE_ADDR']
    fileName = '/tmp/deployRecycle_' + getNowTime()
    deploy = deployWwwRecycle.delay(env,site,username,ip,fileName)
    if deploy.id:
        return render_to_response('getText.html')
    else:
        return HttpResponse('celery error!')



