# coding:utf8
from crontab import CronTab
import commands

from project_crontab import models


def syncCronHost2DB():
    """
    将服务器上的crontab同步至DB中
    """
    my_cron = CronTab(tabfile='/etc/crontab', user=False)
    for info in my_cron[4:]:
        status, time = commands.getstatusoutput("grep '%s' /var/log/cron.log | tail -n 1 | awk \'{print $1,$2,$3}\'" % info.command)
        