
from django.shortcuts import render,render_to_response,HttpResponse
from django.contrib.auth.decorators import login_required
# Create your views here.
from winservices.models import winconf
import json
from winservices.utils import servicesPublish

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
    env = request.GET['env']
    server = request.GET['services']
    print '---%s----%s--' %(env,server)
    obj = servicesPublish().deployServices(env,server)
    return HttpResponse(obj)
