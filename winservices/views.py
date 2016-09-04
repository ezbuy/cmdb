
from django.shortcuts import render,render_to_response,HttpResponse
from django.contrib.auth.decorators import login_required
# Create your views here.
from winservices.models import winconf
import json
from winservices.utils import servicesPublish
from winservices.models import winconf
from salt.client import LocalClient
from asset.utils import notification,logs


@login_required
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
def deployService(request):
    username = request.user
    ip = request.META['REMOTE_ADDR']
    env = request.GET['env']
    server = request.GET['services']

    obj = servicesPublish(username,ip).deployServices(env,server)
    return render(request,'getdata.html',{'result':obj})

@login_required
def winServicesList(request):

    if 'env' in request.GET:
        env = request.GET['env']
    else:
        env = 1
    winServices = winconf.objects.filter(env=int(env))
    return render(request,'winserviceslist.html',{'project':winServices})

@login_required
def winServicesRestart(request):
    data = request.GET.getlist('id')
    action = request.GET['action']
    username = request.user
    ip = request.META['REMOTE_ADDR']

    result = servicesPublish(username,ip).servicesAction(data,action)

    return render(request,'getdata.html',{'result':result})
