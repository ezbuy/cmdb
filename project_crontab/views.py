# coding:utf8
from django.shortcuts import render, render_to_response, HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from crontab import CronTab
import getopt
import commands
import re

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
         'project_name': svn_obj.project_name,
         'salt_name': svn_obj.salt_minion.saltname,
         'salt_ip': svn_obj.salt_minion.ip,
         'repo': svn_obj.repo,
         'local_path': svn_obj.local_path,
         'create_time': svn_obj.create_time}
        if svn_obj.creator.first_name or svn_obj.creator.last_name
        else
        {'creator_name': svn_obj.creator.username,
         'id': svn_obj.id,
         'project_name': svn_obj.project_name,
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
    print 'keys : ', request.POST.keys()
    project_name = request.POST['project_name']
    print 'project_name : ', project_name
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
            models.Svn.objects.create(project_name=project_name, salt_minion=minion_obj, repo=repo, local_path=local_path, username=username,
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


# @login_required
# def cronProjectList(request):
#     svn_objs = models.Svn.objects.all().order_by('salt_minion__saltname', 'create_time')
#     project_objs = models.Project.objects.all().order_by('name')
#     project_list = [
#         {'creator_name': svn_obj.creator.first_name + svn_obj.creator.last_name,
#          'id': svn_obj.id,
#          'name': svn_obj.name,
#          'path': svn_obj.path,
#          'svn_url': svn_obj.svn.repo,
#          'create_time': svn_obj.create_time}
#         if svn_obj.creator.first_name or svn_obj.creator.last_name
#         else
#         {'creator_name': svn_obj.creator.username,
#          'id': svn_obj.id,
#          'name': svn_obj.name,
#          'path': svn_obj.path,
#          'svn_url': svn_obj.svn.repo,
#          'create_time': svn_obj.create_time}
#         for svn_obj in project_objs]
#     return render(request, 'project_crontab/project_list.html', {'project_list': project_list, 'svn_objs': svn_objs})

#
# @login_required
# def addCronProject(request):
#     errcode = 0
#     msg = 'ok'
#     user = request.user
#     svn_id = request.POST['svn_id']
#     name = request.POST['name'].strip()
#     path = request.POST['path'].strip()
#     try:
#         svn_obj = models.Svn.objects.get(id=int(svn_id))
#     except models.Svn.DoesNotExist:
#         errcode = 500
#         msg = u'crontab SVN不存在'
#     else:
#         try:
#             models.Project.objects.get(svn=svn_obj, name=name, path=path)
#         except models.Project.DoesNotExist:
#             models.Project.objects.create(svn=svn_obj, name=name, path=path, creator=user)
#         else:
#             errcode = 500
#             msg = u'相同项目已存在'
#     data = dict(code=errcode, msg=msg)
#     return HttpResponse(json.dumps(data), content_type='application/json')
#
#
# @login_required
# def delCronProject(request):
#     errcode = 0
#     msg = 'ok'
#     svn_ids = request.POST.getlist('svn_ids', [])
#     del_svn_ids = [int(i) for i in svn_ids]
#     svn_objs = models.Project.objects.filter(id__in=del_svn_ids)
#     if len(svn_objs) == 0:
#         errcode = 500
#         msg = u'选中的项目在数据库中不存在'
#     else:
#         svn_objs.delete()
#     data = dict(code=errcode, msg=msg)
#     return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def crontabList(request):
    page = request.GET.get('page', 1)
    svn_objs = models.Svn.objects.all().order_by('project_name', '-create_time')
    svn_list = [
        {'id': svn_obj.id,
         'name': svn_obj.project_name,
         'local_path': svn_obj.local_path,
         'svn_url': svn_obj.repo,
         }
        if svn_obj.creator.first_name or svn_obj.creator.last_name
        else
        {'id': svn_obj.id,
         'name': svn_obj.project_name,
         'local_path': svn_obj.local_path,
         'svn_url': svn_obj.repo,
         }
        for svn_obj in svn_objs]
    crontab_objs = models.CrontabCmd.objects.all().order_by('-create_time')
    paginator = Paginator(crontab_objs, 20)
    try:
        crontab_list = paginator.page(page)
    except PageNotAnInteger:
        crontab_list = paginator.page(1)
    except EmptyPage:
        crontab_list = paginator.page(paginator.num_pages)

    return render(request, 'project_crontab/crontab_list.html', {'crontab_list': crontab_list, 'svn_list': svn_list})


@login_required
def addCrontab(request):
    errcode = 0
    msg = 'ok'
    user = request.user
    svn_id = request.POST['svn_id']
    cmd = request.POST['cmd'].strip()
    frequency = request.POST['frequency'].strip()
    try:
        svn_obj = models.Svn.objects.get(id=int(svn_id))
    except models.Svn.DoesNotExist:
        errcode = 500
        msg = u'所选SVN不存在'
    else:
        try:
            models.CrontabCmd.objects.get(svn=svn_obj, cmd=cmd, frequency=frequency)
        except models.CrontabCmd.DoesNotExist:
            path = svn_obj.local_path
            cmd_list = cmd.strip().split(' ')
            args_list = []
            opts_dict = {}
            if ' -' not in cmd:
                # 没有参数的命令
                auto_cmd = path + cmd
            else:
                # 有参数的命令
                options, args = getopt.getopt(cmd_list, "hc:f:d:s:n:")
                for opt in args:
                    if opt.startswith('-'):
                        index = args.index(opt)
                        args_list = args[:index]
                        key_list = args[index::2]
                        value_list = args[index+1::2]
                        opts_dict = dict(zip(key_list, value_list))
                        break
                auto_cmd = path + ' '.join(args_list) + ' '

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

                auto_cmd += '>> ' + path + log_name + ' 2>&1' + '\n'
            else:
                auto_cmd += auto_cmd + '\n'

            # 机器上新增
            my_cron = CronTab(tabfile='/etc/crontab', user=False)
            job = my_cron.new(command=auto_cmd, user='root')
            job.setall(frequency.strip())
            job.enable(False)
            # my_cron.write()

            # DB中新增
            if job.is_valid():
                is_valid = 1
            else:
                is_valid = 2
            models.CrontabCmd.objects.create(svn=svn_obj, cmd=cmd, auto_cmd=auto_cmd, is_valid=is_valid, frequency=frequency, creator=user)
        else:
            errcode = 500
            msg = u'相同Crontab Cmd已存在'
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def delCrontab(request):
    errcode = 0
    msg = 'ok'
    cron_ids = request.POST.getlist('svn_ids', [])
    del_cron_ids = [int(i) for i in cron_ids]
    cron_objs = models.CrontabCmd.objects.filter(id__in=del_cron_ids)
    # 在机器上暂停任务
    my_cron = CronTab(tabfile='/etc/crontab', user=False)
    for cron_obj in cron_objs:
        auto_cmd = cron_obj.auto_cmd.strip()
        print 'delCrontab---auto_cmd : '
        print auto_cmd
        for job in my_cron[4:]:
            if job.command == auto_cmd:
                job.enable(False)
                print 'delCrontab----disable---done'
                my_cron.write()
                break

    # 在DB中删除任务
    if len(cron_objs) == 0:
        errcode = 500
        msg = u'选中的项目在数据库中不存在'
    else:
        cron_objs.delete()

    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def startCrontab(request):
    errcode = 0
    msg = 'ok'
    crontab_id = int(request.POST['crontab_id'])
    print 'startCrontab----crontab_id : ', crontab_id
    try:
        crontab_obj = models.CrontabCmd.objects.get(id=crontab_id)
    except models.CrontabCmd.DoesNotExist:
        errcode = 500
        msg = u'所选Crontab在数据库中不存在'
    else:
        # 修改机器上crontab状态为启动
        my_cron = CronTab(tabfile='/etc/crontab', user=False)
        auto_cmd = crontab_obj.auto_cmd.strip()
        print 'startCrontab---auto_cmd : '
        print auto_cmd
        for job in my_cron[4:]:
            if job.command == auto_cmd:
                job.enable()
                print 'startCrontab----enable---done'
                my_cron.write()
                break

        # 修改数据库中cmd状态
        crontab_obj.cmd_status = 2
        crontab_obj.save()
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def pauseCrontab(request):
    errcode = 0
    msg = 'ok'
    crontab_id = int(request.POST['crontab_id'])
    print 'pauseCrontab----crontab_id : ', crontab_id
    try:
        crontab_obj = models.CrontabCmd.objects.get(id=crontab_id)
    except models.CrontabCmd.DoesNotExist:
        errcode = 500
        msg = u'所选Crontab在数据库中不存在'
    else:
        # 修改机器上crontab状态为暂停
        my_cron = CronTab(tabfile='/etc/crontab', user=False)
        auto_cmd = crontab_obj.auto_cmd.strip()
        print 'pauseCrontab---auto_cmd : '
        print auto_cmd
        for job in my_cron[4:]:
            if job.command == auto_cmd:
                job.enable(False)
                print 'pauseCrontab----disable---done'
                my_cron.write()
                break

        # 修改数据库中cmd状态
        crontab_obj.cmd_status = 1
        crontab_obj.save()
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')

