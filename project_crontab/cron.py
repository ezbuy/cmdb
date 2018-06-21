# coding:utf8
from crontab import CronTab
import commands
import sys
import croniter

reload(sys)
sys.setdefaultencoding('utf-8')

from project_crontab import models


def syncCronHost2DB():
    """
    将服务器上的crontab同步至DB中
    """
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
                frequency = str(job).split('root')[0].strip()
                models.CrontabCmd.objects.create(project=None, cmd=job.command, auto_cmd=job.command, is_valid=is_valid, frequency=frequency, cmd_status=2, last_run_time=None, last_run_result=None)
            else:
                print 'already exist in DB'
