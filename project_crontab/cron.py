# coding:utf8
from crontab import CronTab
import commands
import sys
import croniter
import socket
import traceback

from project_crontab import models
from asset import models as asset_models

reload(sys)
sys.setdefaultencoding('utf-8')


def syncCronHost2DB():
    """
    将服务器上的crontab同步至DB中
    """
    res = True
    hostname = socket.gethostname()
    try:
        salt_obj = asset_models.minion.objects.get(saltname=hostname)
    except asset_models.minion.DoesNotExist:
        res = False
    else:
        my_cron = CronTab(tabfile='/etc/crontab', user=False)
        for job in my_cron:
            project_name = job.command.split(' ')[0].split('/')[-1]
            job_frequency = str(job).split(project_name)[0].strip('#').strip()
            if job_frequency == '@hourly':
                job_frequency = '0 * * * *'
            elif job_frequency == '@daily':
                job_frequency = '0 0 * * *'
            elif job_frequency == '@yearly':
                job_frequency = '0 0 1 1 *'

            try:
                models.CrontabCmd.objects.get(auto_cmd=job.command, frequency=job_frequency)
            except models.CrontabCmd.DoesNotExist:
                if job.is_enabled():
                    cmd_status = 2
                else:
                    cmd_status = 1

                last_run_time = job.schedule().get_prev()

                try:
                    svn_obj = asset_models.crontab_svn.objects.get(hostname=salt_obj, project=project_name)
                except asset_models.crontab_svn.DoesNotExist:
                    print ' '
                    print job.command
                    print 'Svn.DoesNotExist'
                else:
                    try:
                        models.CrontabCmd.objects.create(svn=svn_obj, cmd=job.command, auto_cmd=job.command, frequency=job_frequency, cmd_status=cmd_status, last_run_time=last_run_time)
                        print 'create--ok'
                    except Exception as e:
                        print ' '
                        print job.command
                        print 'create Exception---', traceback.print_exc()
            else:
                print 'ct cmd already exist in DB'
    return res
