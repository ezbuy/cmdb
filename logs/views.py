from django.shortcuts import render,render_to_response,HttpResponse
from django.contrib.auth.decorators import login_required
# Create your views here.
from logs.models import *

@login_required
def logs(request):
    logs = goLog.objects.all().order_by('-id')[:10]
    return render(request,'logs/logs.html',{'logs':logs})
