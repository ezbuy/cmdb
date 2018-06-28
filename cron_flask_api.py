#!/usr/local/bin/python
# coding=utf-8

from flask import Flask, request, jsonify
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mico.settings')
django.setup()
import requests
import getopt
import functools
from datetime import datetime
from crontab import CronTab
from django.contrib import auth
from django.db import connection
from django.contrib.auth.models import User

from asset import models as asset_models
from project_crontab import models
from project_crontab import utils
from mico.settings import svn_username, svn_password, go_local_path, svn_repo_url

app = Flask(__name__)


def login_author(func):
    @functools.wraps(func)
    def login_wrapper(*args, **kwargs):
        try:
            username = request.form.get('username')
            password = request.form.get('password')
        except:
            return jsonify({'result': 'username or password is error'})

        if auth.authenticate(username=username, password=password) is not None:
            connection.close()
            if request.form.get('env') is None:
                env = {'env': '1'}
            elif int(request.form.get('env')) not in [1, 2]:
                return jsonify({'result': 'The env not found.!!'})
            else:
                env = {'env': request.form.get('env')}
            request.form().update(env)
            return func(*args, **kwargs)
        else:
            return jsonify({'result': 'username or password is error'})
    return login_wrapper


@app.route('/', methods=['POST'])
# @login_author
def message():
    print request.form.get('env')
    return jsonify({'hi': 'hello world!!'})


@app.route('/cron/add', methods=['POST'])
# @login_author
def add_cron():
    errcode = 0
    msg = 'ok'
    username = request.form.get('username')
    minion_id = request.form.get('minion_id')
    cmd = request.form.get('cmd').strip()
    frequency = request.form.get('frequency').strip()
    try:
        minion_obj = asset_models.minion.objects.get(id=int(minion_id))
    except asset_models.minion.DoesNotExist:
        errcode = 500
        msg = u'所选Salt机器不存在'
    else:
        salt_hostname = minion_obj.saltname
        project_name = cmd.strip().split(' ')[0]
        try:
            svn_obj = asset_models.crontab_svn.objects.get(project=project_name, hostname=minion_obj)
        except asset_models.crontab_svn.DoesNotExist:
            errcode = 500
            msg = u'Crontab Svn不存在'
            return errcode, msg
        else:
            # 创建Crontab CMD
            try:
                models.CrontabCmd.objects.get(svn=svn_obj, cmd=cmd, frequency=frequency)
            except models.CrontabCmd.DoesNotExist:
                # salt机器上拉svn目录
                repo = svn_repo_url + project_name
                errcode, msg = utils.salt_run_sls(username, repo, project_name, salt_hostname)
                if errcode == 0:
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

                    # 机器上创建
                    my_cron = CronTab(tabfile='/etc/crontab', user=False)
                    job = my_cron.new(command=auto_cmd, user='root')
                    job.setall(frequency.strip())
                    job.enable(False)
                    my_cron.write()

                    # DB中创建
                    user_obj = User.objects.get(username=username)
                    models.CrontabCmd.objects.create(svn=svn_obj, cmd=cmd, auto_cmd=auto_cmd, frequency=frequency,
                                                     creator=user_obj)
            else:
                errcode = 500
                msg = u'相同Crontab Cmd已存在'
    data = dict(code=errcode, msg=msg)
    return jsonify(data)


@app.route('/cron/modify', methods=['POST'])
# @login_author
def modify_cron():
    errcode = 0
    msg = 'ok'
    username = request.form.get('username')
    crontab_id = request.form.get('crontab_id')
    minion_id = request.form.get('minion_id')
    try:
        crontab_obj = models.CrontabCmd.objects.get(id=crontab_id)
    except models.CrontabCmd.DoesNotExist:
        errcode = 500
        msg = u'所选Crontab在数据库中不存在'
    else:
        # 在机器上暂停任务
        my_cron = CronTab(tabfile='/etc/crontab', user=False)
        auto_cmd = crontab_obj.auto_cmd.strip()
        print 'modify_cron---auto_cmd : '
        print auto_cmd
        for job in my_cron[4:]:
            if job.command == auto_cmd:
                job.enable(False)
                print 'del_cron----disable---done'
                my_cron.write()
                break

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
                # 在新机器上拉svn，添加crontab
                # 新机器上拉svn目录
                repo = svn_repo_url + project_name
                errcode, msg = utils.salt_run_sls(username, repo, project_name, salt_hostname)
                if errcode == 0:
                    # 新机器上创建
                    my_cron = CronTab(tabfile='/etc/crontab', user=False)
                    job = my_cron.new(command=auto_cmd, user='root')
                    job.setall(crontab_obj.frequency.strip())
                    job.enable(False)
                    my_cron.write()
                # DB只修改crontab的svn
                crontab_obj.svn = svn_obj
                user_obj = User.objects.get(username=username)
                crontab_obj.updater = user_obj
                crontab_obj.save()
    data = dict(code=errcode, msg=msg)
    return jsonify(data)


@app.route('/cron/del', methods=['POST'])
# @login_author
def del_cron():
    errcode = 0
    msg = 'ok'
    cron_ids = request.form.get('cron_ids')
    cron_ids_list = cron_ids.strip().strip('[').strip(']').split(',')
    del_cron_ids = [int(i) for i in cron_ids_list]
    cron_objs = models.CrontabCmd.objects.filter(id__in=del_cron_ids)

    # 在机器上暂停任务
    my_cron = CronTab(tabfile='/etc/crontab', user=False)
    for cron_obj in cron_objs:
        auto_cmd = cron_obj.auto_cmd.strip()
        print 'del_cron---auto_cmd : '
        print auto_cmd
        for job in my_cron[4:]:
            if job.command == auto_cmd:
                job.enable(False)
                print 'del_cron----disable---done'
                my_cron.write()
                break

    # 在DB中删除任务
    if len(cron_objs) == 0:
        errcode = 500
        msg = u'选中的项目在数据库中不存在'
    else:
        cron_objs.delete()
    data = dict(code=errcode, msg=msg)
    return jsonify(data)


@app.route('/cron/start', methods=['POST'])
# @login_author
def start_cron():
    errcode = 0
    msg = 'ok'
    username = request.form.get('username')
    crontab_id = request.form.get('crontab_id')
    try:
        crontab_obj = models.CrontabCmd.objects.get(id=crontab_id)
    except models.CrontabCmd.DoesNotExist:
        errcode = 500
        msg = u'所选Crontab在数据库中不存在'
    else:
        # 修改机器上crontab状态为启动
        my_cron = CronTab(tabfile='/etc/crontab', user=False)
        auto_cmd = crontab_obj.auto_cmd.strip()
        print 'start_cron---auto_cmd : '
        print auto_cmd
        for job in my_cron[4:]:
            if job.command == auto_cmd:
                job.enable()
                print 'start_cron----enable---done'
                my_cron.write()
                break

        # 修改数据库中cmd状态
        user_obj = User.objects.get(username=username)
        crontab_obj.cmd_status = 2
        crontab_obj.updater = user_obj
        crontab_obj.update_time = datetime.now()
        crontab_obj.save()
    data = dict(code=errcode, msg=msg)
    return jsonify(data)


@app.route('/cron/pause', methods=['POST'])
# @login_author
def pause_cron():
    errcode = 0
    msg = 'ok'
    username = request.form.get('username')
    crontab_id = request.form.get('crontab_id')
    try:
        crontab_obj = models.CrontabCmd.objects.get(id=crontab_id)
    except models.CrontabCmd.DoesNotExist:
        errcode = 500
        msg = u'所选Crontab在数据库中不存在'
    else:
        # 修改机器上crontab状态为启动
        my_cron = CronTab(tabfile='/etc/crontab', user=False)
        auto_cmd = crontab_obj.auto_cmd.strip()
        print 'start_cron---auto_cmd : '
        print auto_cmd
        for job in my_cron[4:]:
            if job.command == auto_cmd:
                job.enable(False)
                print 'start_cron----enable---done'
                my_cron.write()
                break

        # 修改数据库中cmd状态
        user_obj = User.objects.get(username=username)
        crontab_obj.cmd_status = 1
        crontab_obj.updater = user_obj
        crontab_obj.update_time = datetime.now()
        crontab_obj.save()
    data = dict(code=errcode, msg=msg)
    return jsonify(data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
    # app.run(host='127.0.0.1', port=5001)
