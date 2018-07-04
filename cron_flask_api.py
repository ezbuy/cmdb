#!/usr/local/bin/python
# coding=utf-8

import commands
from flask import Flask, request, jsonify
import os
from crontab import CronTab

app = Flask(__name__)


@app.route('/', methods=['POST'])
def message():
    return jsonify({'hi': 'hello world!!'})


@app.route('/cron/add', methods=['POST'])
def add_cron():
    errcode = 0
    msg = 'ok'
    auto_cmd = request.form.get('auto_cmd').strip()
    frequency = request.form.get('frequency').strip()
    project_name = request.form.get('project_name').strip()

    # 机器上/etc/crontab中试图创建
    my_cron = CronTab(tabfile='/etc/crontab', user=False)
    create_res = False
    # 判断是否已经存在，已存在则不用新建
    for job in my_cron:
        if job.command.strip() == auto_cmd.strip():
            job_frequency = str(job).split(project_name)[0].strip('#').strip()
            if job_frequency == '@hourly':
                job_frequency = '0 * * * *'
            elif job_frequency == '@daily':
                job_frequency = '0 0 * * *'
            elif job_frequency == '@yearly':
                job_frequency = '0 0 1 1 *'

            if job_frequency == frequency:
                job.enable(False)
                my_cron.write()
                create_res = True
                break
    if not create_res:
        job = my_cron.new(command=auto_cmd, user=project_name)
        job.setall(frequency.strip())
        job.enable(False)
        my_cron.write()

    data = dict(code=errcode, msg=msg)
    return jsonify(data)


@app.route('/cron/del', methods=['POST'])
def del_cron():
    errcode = 0
    msg = 'ok'
    auto_cmd = request.form.get('auto_cmd').strip()
    frequency = request.form.get('frequency').strip()
    project_name = request.form.get('project_name').strip()

    # 在机器上暂停任务
    my_cron = CronTab(tabfile='/etc/crontab', user=False)
    auto_cmd = auto_cmd
    for job in my_cron:
        if job.command == auto_cmd:
            job_frequency = str(job).split(project_name)[0].strip('#').strip()
            if job_frequency == '@hourly':
                job_frequency = '0 * * * *'
            elif job_frequency == '@daily':
                job_frequency = '0 0 * * *'
            elif job_frequency == '@yearly':
                job_frequency = '0 0 1 1 *'

            if job_frequency == frequency:
                job.enable(False)
                my_cron.write()
                break

    data = dict(code=errcode, msg=msg)
    return jsonify(data)

#
# @app.route('/cron/multidel', methods=['POST'])
# def multi_del_cron():
#     errcode = 0
#     msg = 'ok'
#     cron_ids_str = request.form.get('cron_ids_str')
#
#
#     # 在机器上暂停任务
#     my_cron = CronTab(tabfile='/etc/crontab', user=False)
#     for cron_obj in cron_objs:
#         auto_cmd = cron_obj.auto_cmd.strip()
#         for job in my_cron:
#             if job.command == auto_cmd:
#                 job_frequency = str(job).split(cron_obj.svn.project)[0].strip('#').strip()
#                 if job_frequency == '@hourly':
#                     job_frequency = '0 * * * *'
#                 elif job_frequency == '@daily':
#                     job_frequency = '0 0 * * *'
#                 elif job_frequency == '@yearly':
#                     job_frequency = '0 0 1 1 *'
#                 if job_frequency == cron_obj.frequency:
#                     job.enable(False)
#                     my_cron.write()
#
#     data = dict(code=errcode, msg=msg)
#     return jsonify(data)


@app.route('/cron/start', methods=['POST'])
def start_cron():
    errcode = 0
    msg = 'ok'
    auto_cmd = request.form.get('auto_cmd').strip()
    frequency = request.form.get('frequency').strip()
    project_name = request.form.get('project_name').strip()
    # 修改机器上crontab状态为启动
    my_cron = CronTab(tabfile='/etc/crontab', user=False)
    for job in my_cron:
        if job.command == auto_cmd:
            job_frequency = str(job).split(project_name)[0].strip('#').strip()
            if job_frequency == '@hourly':
                job_frequency = '0 * * * *'
            elif job_frequency == '@daily':
                job_frequency = '0 0 * * *'
            elif job_frequency == '@yearly':
                job_frequency = '0 0 1 1 *'
            if job_frequency == frequency:
                job.enable()
                my_cron.write()
                break

    data = dict(code=errcode, msg=msg)
    return jsonify(data)


@app.route('/cron/pause', methods=['POST'])
def pause_cron():
    errcode = 0
    msg = 'ok'
    auto_cmd = request.form.get('auto_cmd').strip()
    frequency = request.form.get('frequency').strip()
    project_name = request.form.get('project_name').strip()
    # 修改机器上crontab状态为启动
    my_cron = CronTab(tabfile='/etc/crontab', user=False)
    for job in my_cron:
        if job.command == auto_cmd:
            job_frequency = str(job).split(project_name)[0].strip('#').strip()
            if job_frequency == '@hourly':
                job_frequency = '0 * * * *'
            elif job_frequency == '@daily':
                job_frequency = '0 0 * * *'
            elif job_frequency == '@yearly':
                job_frequency = '0 0 1 1 *'
            if job_frequency == frequency:
                job.enable(False)
                my_cron.write()
                break

    data = dict(code=errcode, msg=msg)
    return jsonify(data)


@app.route('/cron/last_run_time', methods=['POST'])
def last_run_time():
    errcode = 0
    msg = 'ok'
    data = {}
    my_cron = CronTab(tabfile='/etc/crontab', user=False)
    crontab_ids = request.form.keys()
    for crontab_id in crontab_ids:
        auto_cmd = request.form.get(crontab_id).strip()
        print 'auto_cmd : ', auto_cmd
        for job in my_cron:
            print job.command
            if job.command == auto_cmd:
                log_cmd = "grep '%s' /var/log/cron.log | tail -n 1 | awk \'{print $1,$2,$3}\'" % job.command
                print '**************'
                print log_cmd
                status, last_run_time = commands.getstatusoutput(log_cmd)
                print status, last_run_time
                print '^^^^^^^^^^^^^^^^^'
                if last_run_time:
                    data[crontab_id] = last_run_time

    data = dict(code=errcode, msg=msg, data=data)
    return jsonify(data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
    # app.run(host='127.0.0.1', port=5001)
