# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


# Create your models here.
class BaseModel(models.Model):
    id = models.AutoField(primary_key=True)
    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Project(BaseModel):
    name = models.CharField(max_length=128, unique=True, help_text=u'项目名称')
    owner = models.CharField(max_length=256, help_text=u'项目负责人')
    state = models.SmallIntegerField(default=0, help_text=u'项目状态，默认启用，0：启用，1：禁用')


class Item(BaseModel):
    ITEM_REFS = (
        ('Graphite', 'Graphite'),
    )

    pid = models.IntegerField(help_text=u'关联项目')
    key = models.CharField(max_length=128, unique=True, help_text=u'监控项key值')
    ref = models.CharField(max_length=64, choices=ITEM_REFS, help_text=u'监控项数据来源')
    name = models.CharField(max_length=256, help_text=u'监控项名称')
    state = models.SmallIntegerField(default=0, help_text=u'监控项状态，默认启用，0：启用，1：禁用')
    interval = models.IntegerField(default=60, help_text=u'间隔时间（秒），默认60秒')


class Trigger(BaseModel):
    item_id = models.IntegerField(help_text=u'关联监控项')
    expr = models.CharField(max_length=1024, help_text=u'触发器规则')
    error = models.CharField(max_length=2048, help_text=u'告警信息')
    recovery = models.CharField(max_length=2048, help_text=u'恢复信息')
    state = models.SmallIntegerField(default=0, help_text=u'触发器状态，默认启用，0：启用，1：禁用')
    value = models.SmallIntegerField(default=0, help_text=u'触发器执行结果，默认正常，0：正常，1：告警')
    clock = models.IntegerField(help_text=u'触发器执行时间')


class Message(BaseModel):
    alert_id = models.IntegerField(default=0, help_text=u'关联已发送告警')
    item_id = models.IntegerField(help_text=u'关联监控项')
    tid = models.IntegerField(help_text=u'关联触发器')
    msg = models.CharField(max_length=2048, help_text=u'信息内容')
    clock = models.IntegerField(help_text=u'信息触发时间')
    value = models.SmallIntegerField(default=0, help_text=u'信息类型，默认error，0：error，1：recovery')


class Alert(BaseModel):
    ALERT_TYPES = (
        ('ding', 'dingtalk'),
    )

    pid = models.IntegerField(help_text=u'关联项目')
    msg = models.CharField(max_length=2048, help_text=u'告警内容')
    type = models.CharField(max_length=128, choices=ALERT_TYPES, help_text=u'告警发送类型')
    clock = models.IntegerField(help_text=u'告警发送时间')
    sendto = models.CharField(max_length=2048, help_text=u'告警接收人')
    is_sent = models.SmallIntegerField(default=0, help_text=u'告警是否发送，0：已发送，1：发送失败')
