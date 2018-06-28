# coding:utf8
import requests

from django.shortcuts import render, render_to_response, HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from asset.utils import *
from asset import models as asset_models
# from project_crontab import utils
from project_crontab import models


@login_required
def crontabList(request):
    page = request.GET.get('page', 1)
    minion_objs = asset_models.minion.objects.all().order_by('saltname')
    minion_list = [
        {'id': minion_obj.id,
         'hostname': minion_obj.saltname,
         'ip': minion_obj.ip,
         }
        for minion_obj in minion_objs]

    crontab_objs = models.CrontabCmd.objects.all().order_by('-create_time')
    paginator = Paginator(crontab_objs, 20)
    try:
        crontab_list = paginator.page(page)
    except PageNotAnInteger:
        crontab_list = paginator.page(1)
    except EmptyPage:
        crontab_list = paginator.page(paginator.num_pages)

    return render(request, 'project_crontab/crontab_list.html', {'crontab_list': crontab_list, 'minion_list': minion_list})


@login_required
def addCrontab(request):
    login_user = request.user
    minion_id = request.POST['minion_id']
    cmd = request.POST['cmd'].strip()
    frequency = request.POST['frequency'].strip()

    postData = {
        'username': login_user.username,
        'password': login_user.password,
        'minion_id': minion_id,
        'cmd': cmd,
        'frequency': frequency,
    }
    response = requests.post('http://116.196.87.93:5001/cron/add', data=postData)
    print 'response.text'
    print response.text
    errcode, msg = 0, 'ok'

    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def modifyCrontab(request):
    login_user = request.user
    crontab_id = int(request.POST['crontab_id'])
    minion_id = int(request.POST['minion_id'])

    postData = {
        'username': login_user.username,
        'crontab_id': crontab_id,
        'minion_id': minion_id,
    }
    response = requests.post('http://116.196.87.93:5001/cron/modify', data=postData)
    print response.text
    errcode, msg = 0, 'ok'

    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def delCrontab(request):
    cron_ids = request.POST.getlist('cron_ids', [])

    postData = {
        'cron_ids': cron_ids,
    }
    response = requests.post('http://116.196.87.93:5001/cron/del', data=postData)
    print response.text
    errcode, msg = 0, 'ok'

    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def startCrontab(request):
    login_user = request.user
    crontab_id = int(request.POST['crontab_id'])
    postData = {
        'username': login_user.username,
        'crontab_id': crontab_id,
    }
    response = requests.post('http://116.196.87.93:5001/cron/start', data=postData)
    print response.text
    errcode, msg = 0, 'ok'
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def pauseCrontab(request):
    login_user = request.user
    crontab_id = int(request.POST['crontab_id'])
    postData = {
        'username': login_user.username,
        'crontab_id': crontab_id,
    }
    response = requests.post('http://116.196.87.93:5001/cron/pause', data=postData)
    print response.text
    errcode, msg = 0, 'ok'
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')

