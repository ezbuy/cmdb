# coding:utf8
from django.shortcuts import render, render_to_response, HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from asset.utils import *
from asset import models as asset_models
# from project_crontab import utils
from project_crontab import models


@login_required
def crontabList(request):
    login_user = request.user
    local_ip = request.META['REMOTE_ADDR']
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
    local_ip = request.META['REMOTE_ADDR']
    minion_id = request.POST['minion_id']
    cmd = request.POST['cmd'].strip()
    frequency = request.POST['frequency'].strip()

    try:
        minion_obj = asset_models.minion.objects.get(id=int(minion_id))
    except asset_models.minion.DoesNotExist:
        errcode = 500
        msg = u'所选Salt机器不存在'
    else:
        pass
    errcode, msg = 0, 'ok'
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def modifyCrontab(request):
    login_user = request.user
    local_ip = request.META['REMOTE_ADDR']
    crontab_id = int(request.POST['crontab_id'])

    errcode, msg = 0, 'ok'

    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def delCrontab(request):
    login_user = request.user
    local_ip = request.META['REMOTE_ADDR']
    cron_ids = request.POST.getlist('svn_ids', [])
    del_cron_ids = [int(i) for i in cron_ids]
    errcode, msg = 0, 'ok'
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def startCrontab(request):
    login_user = request.user
    local_ip = request.META['REMOTE_ADDR']
    crontab_id = int(request.POST['crontab_id'])
    errcode, msg = 0, 'ok'
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def pauseCrontab(request):
    login_user = request.user
    local_ip = request.META['REMOTE_ADDR']
    crontab_id = int(request.POST['crontab_id'])
    errcode, msg = 0, 'ok'
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')

