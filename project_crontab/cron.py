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
        for job in my_cron[4:]:
            if job.is_enabled():
                try:
                    models.CrontabCmd.objects.get(auto_cmd=job.command)
                except models.CrontabCmd.DoesNotExist:
                    if job.is_valid():
                        is_valid = 1
                    else:
                        is_valid = 2

                    last_run_time = job.schedule().get_prev()

                    if '*' in str(job):
                        frequency = ' '.join(str(job).strip('#').strip().split(' ')[0:5])
                    else:
                        frequency = str(job).strip('#').strip().split(' ')[0]

                    try:
                        svn_obj = models.Svn.objects.get(salt_minion=salt_obj)
                    except models.Svn.DoesNotExist:
                        print ' '
                        print job.command
                        print 'Svn.DoesNotExist'
                    else:
                        try:
                            models.CrontabCmd.objects.create(svn=svn_obj, cmd=job.command, auto_cmd=job.command, frequency=frequency, cmd_status=2, is_valid=is_valid, last_run_time=last_run_time)
                        except Exception as e:
                            print ' '
                            print job.command
                            print 'create Exception---', traceback.print_exc()
                else:
                    print 'ct cmd already exist in DB'
    return res
