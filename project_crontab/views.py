# coding:utf8
import requests
# import getopt

from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from asset.utils import *
from asset import models as asset_models
from project_crontab import utils
from project_crontab import models
from mico.settings import svn_username, svn_password, go_local_path, svn_repo_url, crontab_flask_port


@login_required
def crontabList(request):
    page = request.GET.get('page', 1)
    minion_objs = asset_models.cron_minion.objects.all().order_by('name')
    crontab_objs = models.CrontabCmd.objects.all().order_by('-create_time')
    minion_list = []

    for minion_obj in minion_objs:
        minion_list.append({'id': minion_obj.id,
                            'alias_name': minion_obj.name,
                            })
        minion_crontab_objs = crontab_objs.filter(svn__minion_hostname=minion_obj)
        postData = {}
        if len(minion_crontab_objs) > 0:
            for minion_cron in minion_crontab_objs:
                postData.update({minion_cron.id: minion_cron.auto_cmd})

            try:
                # 获取last_run_time
                flask_url = 'http://' + minion_obj.saltminion.ip + ':' + crontab_flask_port + '/cron/last_run_time'
                response = requests.post(flask_url, data=postData)
                res_json = response.json()
            except Exception as e:
                print e.message
                errcode = 500
                msg = u'获取last_run_time异常'
            else:
                errcode = res_json['code']
                msg = res_json['msg']
                data = res_json['data']
                if errcode == 0:
                    # 更新crontab的last_run_time
                    for crontab_id in data.keys():
                        try:
                            cron_obj = minion_crontab_objs.get(id=int(crontab_id))
                        except Exception as e:
                            print 'not exist : ', e.message
                        else:
                            cron_obj.last_run_time = data[crontab_id]
                            cron_obj.save()

    paginator = Paginator(crontab_objs, 20)
    try:
        crontab_list = paginator.page(page)
    except PageNotAnInteger:
        crontab_list = paginator.page(1)
    except EmptyPage:
        crontab_list = paginator.page(paginator.num_pages)

    return render(request, 'project_crontab/crontab_list.html',
                  {'crontab_list': crontab_list, 'minion_list': minion_list})


@login_required
def addCrontab(request):
    login_user = request.user
    minion_id = request.POST['minion_id']
    cmd = request.POST['cmd'].strip()
    frequency = request.POST['frequency'].strip()
    frequency = frequency.replace('*/1', '*')
    login_ip = request.META['REMOTE_ADDR']

    cmd_list = cmd.strip().split(' ')
    project_name = cmd_list[0]
    go_group = asset_models.gogroup.objects.filter(name=project_name)
    # 检查crontab cmd命令格式
    if ';' in cmd or '&&' in cmd or '||' in cmd or '>' in cmd or len(go_group) == 0:
        errcode = 500
        msg = u'命令格式有误'
        data = dict(code=errcode, msg=msg)
        return HttpResponse(json.dumps(data), content_type='application/json')

    try:
        minion_obj = asset_models.cron_minion.objects.get(id=int(minion_id))
    except asset_models.cron_minion.DoesNotExist:
        errcode = 500
        msg = u'所选Salt机器不存在'
    else:
        salt_hostname = minion_obj.saltminion.saltname
        repo = svn_repo_url + project_name
        localpath = go_local_path + project_name
        svn_obj = None
        try:
            svn_obj = asset_models.crontab_svn.objects.get(project=project_name, minion_hostname=minion_obj,
                                                           username=svn_username, password=svn_password, repo=repo,
                                                           localpath=localpath)
        except asset_models.crontab_svn.DoesNotExist:
            svn_obj = asset_models.crontab_svn.objects.create(project=project_name, minion_hostname=minion_obj,
                                                              username=svn_username, password=svn_password, repo=repo,
                                                              localpath=localpath, hostname=minion_obj.saltminion)
        finally:
            try:
                models.CrontabCmd.objects.get(svn=svn_obj, cmd=cmd, frequency=frequency)
            except models.CrontabCmd.DoesNotExist:
                # 自动补全命令auto_cmd
                auto_cmd = localpath + '/' + cmd + ' -c ' + '/srv/gotemplate/' + project_name + '/conf.ctmpl'
                log_path = '/var/log/' + project_name + '/'
                log_name = project_name + '_' + cmd_list[1] + '.log'
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
                        'project_name': project_name,
                    }
                    try:
                        flask_url = 'http://' + minion_obj.saltminion.ip + ':' + crontab_flask_port + '/cron/add'
                        response = requests.post(flask_url, data=postData)
                        res_json = response.json()
                    except Exception as e:
                        print e.message
                        errcode = 500
                        msg = u'添加异常'
                    else:
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
    print 'minion_id : ', minion_id
    login_ip = request.META['REMOTE_ADDR']
    try:
        minion_obj = asset_models.cron_minion.objects.get(id=int(minion_id))
    except asset_models.cron_minion.DoesNotExist:
        errcode = 500
        msg = u'所选Salt机器不存在'
    else:
        try:
            crontab_obj = models.CrontabCmd.objects.get(id=crontab_id)
        except models.CrontabCmd.DoesNotExist:
            errcode = 500
            msg = u'所选Crontab在数据库中不存在'
        else:
            project_name = str(crontab_obj.cmd.strip().split(' ')[0].strip())
            # 在机器上暂停任务
            auto_cmd = crontab_obj.auto_cmd.strip()
            frequency = crontab_obj.frequency
            postData = {
                'auto_cmd': auto_cmd,
                'frequency': frequency,
                'project_name': project_name,
            }
            try:
                flask_url = 'http://' + minion_obj.saltminion.ip + ':' + crontab_flask_port + '/cron/del'
                response = requests.post(flask_url, data=postData)
            except Exception as e:
                errcode = 500
                msg = u'删除异常'
            else:
                res_json = response.json()
                errcode = res_json['code']
                msg = res_json['msg']
            if errcode == 0:
                # 暂停成功后
                salt_hostname = minion_obj.saltminion.saltname
                repo = svn_repo_url + project_name
                localpath = go_local_path + project_name

                try:
                    svn_obj = asset_models.crontab_svn.objects.get(project=project_name, minion_hostname=minion_obj,
                                                                   username=svn_username, password=svn_password,
                                                                   repo=repo,
                                                                   localpath=localpath)
                except asset_models.crontab_svn.DoesNotExist:
                    svn_obj = asset_models.crontab_svn.objects.create(project=project_name, minion_hostname=minion_obj,
                                                                      username=svn_username, password=svn_password,
                                                                      repo=repo,
                                                                      localpath=localpath, hostname=minion_obj.saltminion)
                finally:
                    # 新机器上拉svn目录
                    repo = svn_repo_url + project_name
                    errcode, msg = utils.salt_run_sls(login_user, repo, project_name, salt_hostname, login_ip)
                    print 'run salt ok'
                    if errcode == 0:
                        # 新机器上创建
                        postData = {
                            'auto_cmd': auto_cmd,
                            'frequency': frequency,
                            'project_name': project_name,
                        }

                        try:
                            flask_url = 'http://' + minion_obj.saltminion.ip + ':' + crontab_flask_port + '/cron/add'
                            response = requests.post(flask_url, data=postData)
                            print'pull svn ok'
                        except Exception as e:
                            errcode = 500
                            msg = u'添加异常'
                        else:
                            res_json = response.json()
                            errcode = res_json['code']
                            msg = res_json['msg']
                        if errcode == 0:
                            # DB只修改crontab的svn
                            crontab_obj.svn = svn_obj
                            crontab_obj.cmd_status = 1
                            crontab_obj.updater = login_user
                            crontab_obj.save()
                            print 'crontab save ok'

    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def delCrontab(request):
    del_cron_id = request.POST.get('del_cron_id')
    # cron_ids = request.POST.getlist('cron_ids', [])
    # cron_objs = models.CrontabCmd.objects.filter(id__in=cron_ids)
    # errcode = 0
    # msg = 'ok'
    try:
        cron_obj = models.CrontabCmd.objects.get(id=int(del_cron_id))
    except models.CrontabCmd.DoesNotExist:
        errcode = 500
        msg = u'所选Crontab在DB中不存在'
    else:
        # 机器上暂停
        auto_cmd = cron_obj.auto_cmd
        frequency = cron_obj.frequency
        project_name = cron_obj.svn.project
        postData = {
            'auto_cmd': auto_cmd,
            'frequency': frequency,
            'project_name': project_name,
        }
        try:
            flask_url = 'http://' + cron_obj.svn.minion_hostname.saltminion.ip + ':' + crontab_flask_port + '/cron/del'
            response = requests.post(flask_url, data=postData)
        except Exception as e:
            errcode = 500
            msg = u'删除异常'
        else:
            res_json = response.json()
            errcode = res_json['code']
            msg = res_json['msg']
            if errcode == 0:
                # DB中删除
                cron_obj.delete()
        if errcode != 0:
            data = dict(code=errcode, msg=msg)
            return HttpResponse(json.dumps(data), content_type='application/json')
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def startCrontab(request):
    login_user = request.user
    crontab_id = int(request.POST['crontab_id'])
    try:
        crontab_obj = models.CrontabCmd.objects.get(id=crontab_id)
    except models.CrontabCmd.DoesNotExist:
        errcode = 500
        msg = u'所选Crontab在数据库中不存在'
    else:
        postData = {
            'auto_cmd': crontab_obj.auto_cmd,
            'frequency': crontab_obj.frequency,
            'project_name': crontab_obj.svn.project,
        }
        try:
            flask_url = 'http://' + crontab_obj.svn.minion_hostname.saltminion.ip + ':' + crontab_flask_port + '/cron/start'
            response = requests.post(flask_url, data=postData)
        except Exception as e:
            errcode = 500
            msg = u'启动异常'
        else:
            res_json = response.json()
            errcode = res_json['code']
            msg = res_json['msg']
            if errcode == 0:
                # 修改数据库中cmd状态
                user_obj = login_user
                crontab_obj.cmd_status = 2
                crontab_obj.updater = user_obj
                crontab_obj.save()
    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def pauseCrontab(request):
    login_user = request.user
    crontab_id = int(request.POST['crontab_id'])
    try:
        crontab_obj = models.CrontabCmd.objects.get(id=crontab_id)
    except models.CrontabCmd.DoesNotExist:
        errcode = 500
        msg = u'所选Crontab在数据库中不存在'
    else:
        postData = {
            'auto_cmd': crontab_obj.auto_cmd,
            'frequency': crontab_obj.frequency,
            'project_name': crontab_obj.svn.project,
        }
        try:
            flask_url = 'http://' + crontab_obj.svn.minion_hostname.saltminion.ip + ':' + crontab_flask_port + '/cron/pause'
            response = requests.post(flask_url, data=postData)
        except Exception as e:
            errcode = 500
            msg = u'暂停异常'
        else:
            res_json = response.json()
            errcode = res_json['code']
            msg = res_json['msg']
            if errcode == 0:
                # 修改数据库中cmd状态
                user_obj = login_user
                crontab_obj.cmd_status = 1
                crontab_obj.updater = user_obj
                crontab_obj.save()

    data = dict(code=errcode, msg=msg)
    return HttpResponse(json.dumps(data), content_type='application/json')
