# coding:utf8
import requests
import getopt

from django.shortcuts import render, render_to_response, HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from asset.utils import *
from asset import models as asset_models
from project_crontab import utils
from project_crontab import models
from mico.settings import svn_username, svn_password, go_local_path, svn_repo_url


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
    login_ip = request.META['REMOTE_ADDR']

    try:
        minion_obj = asset_models.minion.objects.get(id=int(minion_id))
    except asset_models.minion.DoesNotExist:
        errcode = 500
        msg = u'所选Salt机器不存在'
    else:
        salt_hostname = minion_obj.saltname
        project_name = cmd.strip().split(' ')[0]
        repo = svn_repo_url + project_name
        try:
            svn_obj = asset_models.crontab_svn.objects.get(project=project_name, hostname=minion_obj)
        except asset_models.crontab_svn.DoesNotExist:
            errcode = 500
            msg = u'Crontab Svn不存在'
        else:
            try:
                models.CrontabCmd.objects.get(svn=svn_obj, cmd=cmd, frequency=frequency)
            except models.CrontabCmd.DoesNotExist:
                # 自动补全命令
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
                            value_list = args[index + 1::2]
                            opts_dict = dict(zip(key_list, value_list))
                            break
                    auto_cmd = path + '/' + ' '.join(args_list) + ' '
                log_path = '/var/log/' + project_name + '/'
                if opts_dict:
                    if '-d' in opts_dict.keys():
                        log_name = opts_dict['-d'].split('.')[0] + '.log'
                    elif '-c' in opts_dict.keys():
                        log_name = args_list[0] + '_conf.log'
                    else:
                        log_name = args_list[0] + '.log'
                    for k, v in opts_dict.items():
                        if k == '-c':
                            auto_cmd += k + ' ' + path + '/' + 'conf/' + v + ' '
                        elif k == '-d':
                            auto_cmd += k + ' ' + path + '/' + 'conf/' + v + ' '
                        else:
                            auto_cmd += k + ' ' + v + ' '
                    auto_cmd += '>> ' + log_path + log_name + ' 2>&1' + '\n'
                else:
                    log_name = '_'.join(cmd_list) + '.log'
                    auto_cmd += ' >> ' + log_path + log_name + ' 2>&1' + '\n'
                print 'add_cron--------auto_cmd : '
                print auto_cmd
                print '************'
                # 在salt master上执行salt命令，给minion拉svn
                errcode, msg = utils.salt_run_sls(login_user, repo, project_name, salt_hostname, login_ip)
                if errcode == 0:
                    # 拉svn成功后，在minion机器上部署crontab
                    postData = {
                        'auto_cmd': auto_cmd,
                        'frequency': frequency,
                    }
                    response = requests.post('http://116.196.87.93:5001/cron/add', data=postData)
                    res_json = response.json()
                    errcode = res_json['code']
                    msg = res_json['msg']
                    if errcode == 0:
                        # DB中创建Crontab CMD
                        models.CrontabCmd.objects.create(svn=svn_obj, cmd=cmd, auto_cmd=auto_cmd, frequency=frequency,
                                                         creator=login_user)
            else:
                errcode = 500
                msg = u'相同Crontab Cmd已存在'

    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def modifyCrontab(request):
    login_user = request.user
    crontab_id = int(request.POST['crontab_id'])
    minion_id = int(request.POST['minion_id'])
    login_ip = request.META['REMOTE_ADDR']

    try:
        crontab_obj = models.CrontabCmd.objects.get(id=crontab_id)
    except models.CrontabCmd.DoesNotExist:
        errcode = 500
        msg = u'所选Crontab在数据库中不存在'
    else:
        # 在机器上暂停任务
        auto_cmd = crontab_obj.auto_cmd.strip()
        frequency = crontab_obj.frequency
        postData = {
            'auto_cmd': auto_cmd,
        }
        response = requests.post('http://116.196.87.93:5001/cron/del', data=postData)
        res_json = response.json()
        errcode = res_json['code']
        msg = res_json['msg']
        if errcode == 0:
            # 暂停成功后
            project_name = crontab_obj.cmd.strip().split(' ')[0]
            try:
                minion_obj = asset_models.minion.objects.get(id=int(minion_id))
            except asset_models.minion.DoesNotExist:
                errcode = 500
                msg = u'所选Salt机器不存在'
            else:
                salt_hostname = minion_obj.saltname
                try:
                    svn_obj = asset_models.crontab_svn.objects.get(project=project_name, hostname=minion_obj)
                except asset_models.crontab_svn.DoesNotExist:
                    errcode = 500
                    msg = u'Crontab Svn不存在'
                    return errcode, msg
                else:
                    # 新机器上拉svn目录
                    repo = svn_repo_url + project_name
                    errcode, msg = utils.salt_run_sls(login_user, repo, project_name, salt_hostname, login_ip)
                    if errcode == 0:
                        # 新机器上创建
                        postData = {
                            'auto_cmd': auto_cmd,
                            'frequency': frequency,
                        }
                        response = requests.post('http://116.196.87.93:5001/cron/add', data=postData)
                        res_json = response.json()
                        errcode = res_json['code']
                        msg = res_json['msg']
                        if errcode == 0:
                            # DB只修改crontab的svn
                            crontab_obj.svn = svn_obj
                            user_obj = login_user
                            crontab_obj.cmd_status = 1
                            crontab_obj.updater = user_obj
                            crontab_obj.save()

    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def delCrontab(request):
    cron_ids = request.POST.getlist('cron_ids', [])
    cron_objs = models.CrontabCmd.objects.filter(id__in=cron_ids)

    if len(cron_objs) == 0:
        errcode = 500
        msg = u'选中的项目在数据库中不存在'
    else:
        # 机器上暂停
        postData = {
            'cron_ids': cron_ids,
        }
        response = requests.post('http://116.196.87.93:5001/cron/multidel', data=postData)
        res_json = response.json()
        errcode = res_json['code']
        msg = res_json['msg']

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
    res_json = response.json()
    errcode = res_json['code']
    msg = res_json['msg']
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
    res_json = response.json()
    errcode = res_json['code']
    msg = res_json['msg']
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')

