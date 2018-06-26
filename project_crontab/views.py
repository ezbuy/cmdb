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
from mico.settings import svn_username, svn_password, go_local_path, svn_repo_url
from salt_api.api import SaltApi


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
    errcode = 0
    msg = 'ok'
    user = request.user
    minion_id = request.POST['minion_id']
    cmd = request.POST['cmd'].strip()
    frequency = request.POST['frequency'].strip()
    try:
        minion_obj = asset_models.minion.objects.get(id=int(minion_id))
    except asset_models.minion.DoesNotExist:
        errcode = 500
        msg = u'所选Salt机器不存在'
    else:
        project_name = cmd.strip().split(' ')[0]
        try:
            svn_obj = asset_models.crontab_svn.objects.get(project=project_name, hostname=minion_obj)
        except asset_models.crontab_svn.DoesNotExist:
            repo = svn_repo_url + project_name
            localpath = go_local_path + project_name
            svn_obj = asset_models.crontab_svn.objects.create(project=project_name, hostname=minion_obj, username=svn_username, password=svn_password, repo=repo, localpath=localpath)

        try:
            models.CrontabCmd.objects.get(svn=svn_obj, cmd=cmd, frequency=frequency)
        except models.CrontabCmd.DoesNotExist:
            path = svn_obj.localpath
            cmd_list = cmd.strip().split(' ')
            args_list = []
            opts_dict = {}
            if ' -' not in cmd:
                # 没有参数的命令
                auto_cmd = path + '/' + cmd
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
                auto_cmd = path + '/' + ' '.join(args_list) + ' '

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
                        auto_cmd += k + ' ' + path + '/' + 'conf/' + v + ' '
                    elif k == '-d':
                        auto_cmd += k + ' ' + path + '/' + 'conf/' + v + ' '
                    else:
                        auto_cmd += k + ' ' + v + ' '

                auto_cmd += '>> ' + path + '/' + log_name + ' 2>&1' + '\n'
            else:
                auto_cmd += auto_cmd + '\n'

            # 机器上新增
            # my_cron = CronTab(tabfile='/etc/crontab', user=False)
            # job = my_cron.new(command=auto_cmd, user='root')
            # job.setall(frequency.strip())
            # job.enable(False)
            # my_cron.write()

            models.CrontabCmd.objects.create(svn=svn_obj, cmd=cmd, auto_cmd=auto_cmd, frequency=frequency, creator=user)
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

