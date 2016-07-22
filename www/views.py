from django.shortcuts import render,render_to_response,HttpResponse
from django.contrib.auth.decorators import login_required

# Create your views here.
from www.utils import deployWww
from www.models import webSite
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
     deployWww.delay(env,site)
     return render_to_response('getText.html')
