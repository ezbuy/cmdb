
from django.shortcuts import render,render_to_response,HttpResponse
from django.contrib.auth.decorators import login_required
# Create your views here.
from winservices.models import winconf
import json
from winservices.utils import servicesPublish
from winservices.models import winconf
from salt.client import LocalClient
from asset.utils import notification,logs



def services(request):
    return render_to_response('winservices.html')


def getServicesList(request):
    env = request.GET['env']
    obj = winconf.objects.filter(env=env)
    servicesList = []
    for name in obj:
        servicesList.append(name.servicename)

    return  HttpResponse(json.dumps(servicesList))


def deployService(request):
    username = request.user
    ip = request.META['REMOTE_ADDR']
    env = request.GET['env']
    server = request.GET['services']

    obj = servicesPublish(username,ip).deployServices(env,server)
    return render_to_response('getdata.html',{'result':obj})


def winServicesList(request):

    if 'env' in request.GET:
        env = request.GET['env']
    else:
        env = 1
    winServices = winconf.objects.filter(env=int(env))
    return render_to_response('winserviceslist.html',{'project':winServices})


def winServicesRestart(request):
    data = request.GET.getlist('id')
    salt = LocalClient()
    username = request.user
    ip = request.META['REMOTE_ADDR']
    result = []

    for v in data:
        sName, host = v.split(',')
        getMes = salt.cmd(host, 'cmd.run', ['supervisorctl restart %s' % sName])
        result.append(getMes)
        info = 'restart ' + sName
        notification(host, info, getMes, username)
    logs(username, ip, 'restart services', result)

    return render_to_response('getdata.html',{'result':result})
