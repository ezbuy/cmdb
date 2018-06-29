#!/usr/local/bin/python
# coding=utf-8

from flask import Flask, request, jsonify
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mico.settings')
django.setup()
import functools
from datetime import datetime
from crontab import CronTab
from django.contrib import auth
from django.db import connection
from django.contrib.auth.models import User

from asset import models as asset_models
from project_crontab import models
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
    auto_cmd = request.form.get('auto_cmd').strip()
    frequency = request.form.get('frequency').strip()

    # 机器上/etc/crontab中试图创建
    my_cron = CronTab(tabfile='/etc/crontab', user=False)
    create_res = False
    # 判断是否已经存在，已存在则不用新建
    for job in my_cron:
        if job.command.strip() == auto_cmd.strip():
            job_frequency = str(job).split('root')[0].strip('#').strip()
            if job_frequency == frequency:
                job.enable(False)
                my_cron.write()
                create_res = True
                break
    if not create_res:
        job = my_cron.new(command=auto_cmd, user='root')
        job.setall(frequency.strip())
        job.enable(False)
        my_cron.write()

    data = dict(code=errcode, msg=msg)
    return jsonify(data)


@app.route('/cron/del', methods=['POST'])
# @login_author
def del_cron():
    errcode = 0
    msg = 'ok'
    auto_cmd = request.form.get('auto_cmd')
    frequency = request.form.get('frequency').strip()

    # 在机器上暂停任务
    my_cron = CronTab(tabfile='/etc/crontab', user=False)
    auto_cmd = auto_cmd
    print 'modify_cron---auto_cmd : '
    print auto_cmd
    for job in my_cron:
        if job.command == auto_cmd:
            job_frequency = str(job).split('root')[0].strip('#').strip()
            if job_frequency == frequency:
                job.enable(False)
                my_cron.write()
                break

    data = dict(code=errcode, msg=msg)
    return jsonify(data)


@app.route('/cron/multidel', methods=['POST'])
# @login_author
def multi_del_cron():
    errcode = 0
    msg = 'ok'
    cron_ids = request.form.get('cron_ids')
    print 'cron_ids : ', cron_ids
    cron_ids_list = cron_ids.strip().strip('[').strip(']').split(',')
    del_cron_ids = [int(i) for i in cron_ids_list]
    print 'del_cron_ids : ', del_cron_ids
    cron_objs = models.CrontabCmd.objects.filter(id__in=del_cron_ids)

    # 在机器上暂停任务
    my_cron = CronTab(tabfile='/etc/crontab', user=False)
    for cron_obj in cron_objs:
        auto_cmd = cron_obj.auto_cmd.strip()
        for job in my_cron:
            if job.command == auto_cmd:
                job_frequency = str(job).split('root')[0].strip('#').strip()
                print 'job_frequency : ', job_frequency
                if job_frequency == cron_obj.frequency:
                    job.enable(False)
                    my_cron.write()
    # DB中删除
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
        for job in my_cron:
            if job.command == auto_cmd:
                job_frequency = str(job).split('root')[0].strip('#').strip()
                if job_frequency == crontab_obj.frequency:
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
        print 'pause_cron---auto_cmd : '
        print auto_cmd
        for job in my_cron:
            if job.command == auto_cmd:
                job_frequency = str(job).split('root')[0].strip('#').strip()
                if job_frequency == crontab_obj.frequency:
                    job.enable(False)
                    print 'pause_cron----enable---done'
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
