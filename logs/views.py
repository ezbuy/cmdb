from django.shortcuts import render,render_to_response,HttpResponse
from django.contrib.auth.decorators import login_required
# Create your views here.
from logs.models import *

def gologs(reques):
    logs = goLog.objects.all()
    return render_to_response('logs/gologs.html',{'logs':logs})
