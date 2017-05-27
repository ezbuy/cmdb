# coding: utf-8

from django.db import models
from asset.models import gogroup
# Create your models here.

class monitorProjects(models.Model):
    project_name = models.CharField(max_length=256,verbose_name=u"监控项目名称")
    project_id = models.AutoField(primary=key,verbose_name=u"项目id")
    project_status = models.CharField(max_length=24,verbose_name=u"项目状态")
    project_disable = models.IntegerField(verbose_name=u"项目是否启用")

    def __unicode__(self):
        return self.project_id


class monitorItems(models.Model):
    item_id = models.AutoField(primary=key,verbose_name=u"item id")
    project_id = models.ForeignKey(monitorProjects,verbose_name=u"所属监控项目组")
    item_name = models.CharField(max_length=1024,verbose_name=u"监控item名称")
    item_key = models.CharField(max_length=1024,verbose_name=u"监控item key")
    item_disable = models.IntegerField(verbose_name=u"项目是否启用")
    item_interval = models.IntegerField(verbose_name=u"项目监控间隔")
    item_expression = models.CharField(max_length=1024,verbose_name=u"监控item告警规则")
    item_description = models.CharField(max_length=4096,verbose_name=u"监控item描述")
    item_sendto = models.CharField(max_length=4096,verbose_name=u"监控item接收者")
    item_status = models.CharField(max_length=24,verbose_name=u"item状态")

    def __unicode__(self):
        return self.item_id


class monitorHistory(models.Model):
    clock = models.DateTimeField(auto_now=True, verbose_name=u"监控时间")
    item_id = models.IntegerField(verbose_name=u"item id")
    value = models.CharField(max_length=1024,verbose_name=u"value")


class monitorEvents(models.Model):
    event_id = models.AutoField(primary=key,verbose_name=u"event id")
    clock = models.DateTimeField(auto_now=True, verbose_name=u"监控时间")
    info = models.CharField(max_length=4096,verbose_name=u"告警信息")
    sendto = models.CharField(max_length=4096,verbose_name=u"告警接收者")
    is_send = models.IntegerField(verbose_name=u"是否发送")









