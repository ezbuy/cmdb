# coding:utf8
from django.shortcuts import render, render_to_response, HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import json
import getopt

from asset.utils import *
from project_crontab import models
from asset import models as asset_models
from salt_api.api import SaltApi


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
    repo = request.POST['repo'].strip()
    local_path = request.POST['local_path'].strip()
    username = request.POST['username'].strip()
    password = request.POST['password'].strip()
    try:
        minion_obj = asset_models.minion.objects.get(id=int(salt_id))
    except asset_models.minion.DoesNotExist:
        errcode = 500
        msg = u'salt minion不存在'
    else:
        try:
            models.Svn.objects.get(salt_minion=minion_obj, repo=repo, local_path=local_path)
        except models.Svn.DoesNotExist:
            models.Svn.objects.create(salt_minion=minion_obj, repo=repo, local_path=local_path, username=username,
                                      password=password, creator=user)
        else:
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
    name = request.POST['name'].strip()
    path = request.POST['path'].strip()
    try:
        svn_obj = models.Svn.objects.get(id=int(svn_id))
    except models.Svn.DoesNotExist:
        errcode = 500
        msg = u'crontab SVN不存在'
    else:
        try:
            models.Project.objects.get(svn=svn_obj, name=name, path=path)
        except models.Project.DoesNotExist:
            models.Project.objects.create(svn=svn_obj, name=name, path=path, creator=user)
        else:
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
    page = request.GET.get('page', 1)
    project_objs = models.Project.objects.all().order_by('name', '-create_time')
    project_list = [
        {'id': svn_obj.id,
         'name': svn_obj.name,
         'svn_url': svn_obj.svn.repo,
         }
        if svn_obj.creator.first_name or svn_obj.creator.last_name
        else
        {'id': svn_obj.id,
         'name': svn_obj.name,
         'svn_url': svn_obj.svn.repo,
         }
        for svn_obj in project_objs]
    crontab_objs = models.CrontabCmd.objects.all().order_by('project__name', 'cmd')
    paginator = Paginator(crontab_objs, 20)
    try:
        crontab_list = paginator.page(page)
    except PageNotAnInteger:
        crontab_list = paginator.page(1)
    except EmptyPage:
        crontab_list = paginator.page(paginator.num_pages)
    return render(request, 'project_crontab/crontab_list.html', {'crontab_list': crontab_list, 'project_list': project_list})


@login_required
def addCrontab(request):
    errcode = 0
    msg = 'ok'
    user = request.user
    project_id = request.POST['project_id']
    cmd = request.POST['cmd'].strip()
    frequency = request.POST['frequency'].strip()
    try:
        project_obj = models.Project.objects.get(id=int(project_id))
    except models.Project.DoesNotExist:
        errcode = 500
        msg = u'所选项目不存在'
    else:
        try:
            models.CrontabCmd.objects.get(project=project_obj, cmd=cmd, frequency=frequency)
        except models.CrontabCmd.DoesNotExist:
            path = project_obj.path
            cmd_list = cmd.strip().split(' ')
            args_list = []
            opts_dict = {}
            options, args = getopt.getopt(cmd_list, "hc:f:d:s:n:")
            for opt in args:
                if opt.startswith('-'):
                    index = args.index(opt)
                    args_list = args[:index]
                    key_list = args[index::2]
                    value_list = args[index+1::2]
                    opts_dict = dict(zip(key_list, value_list))
                    break

            auto_cmd = frequency.strip() + ' root ' + path + ' '.join(args_list) + ' '
            print auto_cmd
            if opts_dict:
                if '-d' in opts_dict.keys():
                    log_name = opts_dict['-d'].split('.')[0] + '.log'
                elif '-c' in opts_dict.keys():
                    log_name = args_list[0] + '_conf.log'
                else:
                    log_name = args_list[0] + '.log'
                print 'log_name : '
                print log_name
                for k, v in opts_dict.items():
                    if k == '-c':
                        auto_cmd += k + ' ' + path + 'conf/' + v + ' '
                    elif k == '-d':
                        auto_cmd += k + ' ' + path + 'conf/' + v + ' '
                    else:
                        auto_cmd += k + ' ' + v + ' '

                auto_cmd += '>> ' + path + log_name + ' 2>&1'

            # DB中新增
            models.CrontabCmd.objects.create(project=project_obj, cmd=cmd, auto_cmd=auto_cmd, frequency=frequency, creator=user)
            # 机器上新增
            saltApi = SaltApi()
            salt_host = project_obj.svn.salt_minion.saltname
            pause_auto_cmd = '#' + auto_cmd
            cmd_on_salt = ["echo '%s' >> /etc/crontab" % pause_auto_cmd, 'env={"LC_ALL": "en_US.UTF-8"}']
            # cmd = ["svn checkout %s %s --username=%s --password=%s --non-interactive " % (project_obj.svn.repo, project_obj.svn.local_path, project_obj.svn.username, project_obj.svn.password), 'env={"LC_ALL": "en_US.UTF-8"}']
            print 'cmd_on_salt : '
            print cmd_on_salt
            data = {
                'client': 'local',
                'tgt': salt_host,
                'fun': 'cmd.run',
                'arg': cmd_on_salt
            }
            result = salt_api.salt_cmd(data)
            if result != 0:
                result = result['return']
                print result

            # logs(self.login_user, self.ip, 'update svn', result)

        else:
            errcode = 500
            msg = u'相同Crontab Cmd已存在'
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def delCrontab(request):
    errcode = 0
    msg = 'ok'
    svn_ids = request.POST.getlist('svn_ids', [])
    del_svn_ids = [int(i) for i in svn_ids]
    svn_objs = models.CrontabCmd.objects.filter(id__in=del_svn_ids)
    if len(svn_objs) == 0:
        errcode = 500
        msg = u'选中的项目在数据库中不存在'
    else:
        svn_objs.delete()
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


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
