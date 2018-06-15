# coding:utf8
from django.shortcuts import render, render_to_response, HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required

import json

from asset.utils import *
from project_crontab import models
from asset import models as asset_models


@login_required
def cronSvn(request):
    status = 'ok'
    msg = ''
    if request.POST.keys():
        print 'POST start'
        salt_id = request.POST['salt_id']
        repo = request.POST['repo']
        local_path = request.POST['local_path']
        username = request.POST['username']
        password = request.POST['password']
        try:
            minion_obj = asset_models.minion.objects.get(id=int(salt_id))
        except asset_models.minion.DoesNotExist:
            print 'minion DoesNotExist'
            status = 'failed'
            msg = u'salt minion不存在'
        else:
            try:
                models.Svn.objects.get(salt_minion=minion_obj, repo=repo, local_path=local_path)
            except models.Svn.DoesNotExist:
                models.Svn.objects.create(salt_minion=minion_obj, repo=repo, local_path=local_path, username=username, password=password)
            else:
                print 'already exist svn'
                status = 'failed'
                msg = u'相同svn已存在'

    minion_objs = asset_models.minion.objects.all().order_by('saltname')
    svn_objs = models.Svn.objects.all().order_by('salt_minion__saltname')
    svn_list = [
        {'creator_name': svn_obj.creator.first_name + svn_obj.creator.last_name,
         'id': svn_obj.id,
         'salt_name': svn_obj.salt_minion.saltname,
         'salt_ip': svn_obj.salt_minion.ip,
         'repo': svn_obj.repo,
         'local_path': svn_obj.local_path,
         'create_time': svn_obj.create_time}
        if svn_obj.creator.first_name or svn_obj.creator.last_name
        else
        {'creator_name': svn_obj.creator.username,
         'id': svn_obj.id,
         'salt_name': svn_obj.salt_minion.saltname,
         'salt_ip': svn_obj.salt_minion.ip,
         'repo': svn_obj.repo,
         'local_path': svn_obj.local_path,
         'create_time': svn_obj.create_time}
        for svn_obj in svn_objs]
    result = {'status': status, 'msg': msg}
    return render(request, 'project_crontab/svn_list.html', {'svn_list': svn_list, 'minion_objs': minion_objs, 'result': result})


@login_required
def cronProjectList(request):
    project_list = models.Project.objects.all().order_by('name')
    return render(request, 'project_crontab/project_list.html', {'project_list': project_list})


@login_required
def crontabList(request):
    crontab_list = models.CrontabCmd.objects.all().order_by('project__name', 'cmd')
    return render(request, 'project_crontab/crontab_list.html', {'crontab_list': crontab_list})
