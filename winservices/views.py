
from django.shortcuts import render,render_to_response,HttpResponse
from django.contrib.auth.decorators import login_required
# Create your views here.
from winservices.models import winconf
import json
from winservices.utils import servicesPublish
from winservices.models import winconf
from salt.client import LocalClient
from asset.utils import logs,deny_resubmit


@login_required
@deny_resubmit(page_key='deploy_winservices')
def services(request):
    return render(request,'winservices.html')


@login_required
def getServicesList(request):
    env = request.GET['env']
    obj = winconf.objects.filter(env=env)
    servicesList = []
    for name in obj:
        servicesList.append(name.servicename)

    return  HttpResponse(json.dumps(servicesList))

@login_required
@deny_resubmit(page_key='deploy_winservices')
def deployService(request):
    username = request.user
    ip = request.META['REMOTE_ADDR']
    env = request.POST['env']
    server = request.POST['services']

    obj = servicesPublish(username,ip).deployServices(env,server,request.POST['phone_number'])
    return render(request,'getdata.html',{'result':obj})

@login_required
@deny_resubmit(page_key='deploy_restartservices')
def winServicesList(request):

    if 'env' in request.GET:
        env = request.GET['env']
    else:
        env = 1
    winServices = winconf.objects.filter(env=int(env))
    return render(request,'winserviceslist.html',{'project':winServices})

@login_required
@deny_resubmit(page_key='deploy_restartservices')
def winServicesRestart(request):
    data = request.POST.getlist('id')
    action = request.POST['action']
    username = request.user
    ip = request.META['REMOTE_ADDR']

    result = servicesPublish(username,ip).servicesAction(data,action,request.POST['phone_number'])

    return render(request,'getdata.html',{'result':result})
