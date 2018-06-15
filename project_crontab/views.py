# coding:utf8
from django.shortcuts import render, render_to_response, HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required

import json

from asset.utils import *
from project_crontab import models
from asset import models as asset_models


@login_required
def cronSvn(request):
    minion_objs = asset_models.minion.objects.all().order_by('saltname')
    svn_objs = models.Svn.objects.all().order_by('salt_minion__saltname', 'create_time')
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
    return render(request, 'project_crontab/svn_list.html', {'svn_list': svn_list, 'minion_objs': minion_objs})


@login_required
def addCronSvn(request):
    errcode = 0
    msg = 'ok'
    user = request.user
    salt_id = request.POST['salt_id']
    repo = request.POST['repo']
    local_path = request.POST['local_path']
    username = request.POST['username']
    password = request.POST['password']
    try:
        minion_obj = asset_models.minion.objects.get(id=int(salt_id))
    except asset_models.minion.DoesNotExist:
        print 'minion DoesNotExist'
        errcode = 500
        msg = u'salt minion不存在'
    else:
        try:
            models.Svn.objects.get(salt_minion=minion_obj, repo=repo, local_path=local_path)
        except models.Svn.DoesNotExist:
            models.Svn.objects.create(salt_minion=minion_obj, repo=repo, local_path=local_path, username=username,
                                      password=password, creator=user)
        else:
            print 'already exist svn'
            errcode = 500
            msg = u'相同svn已存在'
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def delCronSvn(request):
    errcode = 0
    msg = 'ok'
    salt_ids = request.POST.getlist('salt_ids', [])
    int_salt_ids = [int(i) for i in salt_ids]
    svn_objs = models.Svn.objects.filter(id__in=int_salt_ids)
    if len(svn_objs) == 0:
        errcode = 500
        msg = u'选中的svn在数据库中不存在'
    else:
        svn_objs.delete()
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def cronProjectList(request):
    svn_objs = models.Svn.objects.all().order_by('salt_minion__saltname', 'create_time')
    project_objs = models.Project.objects.all().order_by('name')
    project_list = [
        {'creator_name': svn_obj.creator.first_name + svn_obj.creator.last_name,
         'id': svn_obj.id,
         'name': svn_obj.name,
         'path': svn_obj.path,
         'svn_url': svn_obj.svn.repo,
         'create_time': svn_obj.create_time}
        if svn_obj.creator.first_name or svn_obj.creator.last_name
        else
        {'creator_name': svn_obj.creator.username,
         'id': svn_obj.id,
         'name': svn_obj.name,
         'path': svn_obj.path,
         'svn_url': svn_obj.svn.repo,
         'create_time': svn_obj.create_time}
        for svn_obj in project_objs]
    return render(request, 'project_crontab/project_list.html', {'project_list': project_list, 'svn_objs': svn_objs})


@login_required
def addCronProject(request):
    errcode = 0
    msg = 'ok'
    user = request.user
    svn_id = request.POST['svn_id']
    name = request.POST['name']
    path = request.POST['path']
    try:
        svn_obj = models.Svn.objects.get(id=int(svn_id))
    except models.Svn.DoesNotExist:
        print 'svn DoesNotExist'
        errcode = 500
        msg = u'crontab SVN不存在'
    else:
        try:
            models.Project.objects.get(svn=svn_obj, name=name, path=path)
        except models.Project.DoesNotExist:
            models.Project.objects.create(svn=svn_obj, name=name, path=path, creator=user)
        else:
            print 'already exist Project'
            errcode = 500
            msg = u'相同项目已存在'
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def delCronProject(request):
    errcode = 0
    msg = 'ok'
    svn_ids = request.POST.getlist('svn_ids', [])
    del_svn_ids = [int(i) for i in svn_ids]
    svn_objs = models.Project.objects.filter(id__in=del_svn_ids)
    if len(svn_objs) == 0:
        errcode = 500
        msg = u'选中的项目在数据库中不存在'
    else:
        svn_objs.delete()
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def crontabList(request):
    crontab_list = models.CrontabCmd.objects.all().order_by('project__name', 'cmd')
    return render(request, 'project_crontab/crontab_list.html', {'crontab_list': crontab_list})


@login_required
def addCrontab(request):
    crontab_list = models.CrontabCmd.objects.all().order_by('project__name', 'cmd')
    return render(request, 'project_crontab/crontab_list.html', {'crontab_list': crontab_list})


@login_required
def delCrontab(request):
    crontab_list = models.CrontabCmd.objects.all().order_by('project__name', 'cmd')
    return render(request, 'project_crontab/crontab_list.html', {'crontab_list': crontab_list})


@login_required
def startCrontab(request):
    crontab_list = models.CrontabCmd.objects.all().order_by('project__name', 'cmd')
    return render(request, 'project_crontab/crontab_list.html', {'crontab_list': crontab_list})


@login_required
def stopCrontab(request):
    crontab_list = models.CrontabCmd.objects.all().order_by('project__name', 'cmd')
    return render(request, 'project_crontab/crontab_list.html', {'crontab_list': crontab_list})


@login_required
def pauseCrontab(request):
    crontab_list = models.CrontabCmd.objects.all().order_by('project__name', 'cmd')
    return render(request, 'project_crontab/crontab_list.html', {'crontab_list': crontab_list})
