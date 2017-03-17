# coding: utf-8
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from asset.models import minion


# Create your models here.

TICKET_STATE = (
    (1, U'新创建'),
    (2, U'进行中'),
    (3, U'已完成'),
    (4, U'拒绝')
)

TICKET_RESULT = (
    (1, U'已执行'),
    (2, U'拒绝'),
    (3, U'进行中')
)

class TicketType(models.Model):
    type_name = models.CharField(max_length=128, verbose_name=u"工单类型")
    handler = models.ManyToManyField(User, verbose_name=u"工单处理人")
    create_time = models.DateTimeField(default= timezone.now, verbose_name=u"工单创建时间")
    modify_time = models.DateTimeField(auto_now=True, verbose_name=u"工单修改时间")
    state = models.IntegerField(choices=TICKET_STATE, blank=True, null=True, verbose_name=u"工单状态")
    hosts = models.ManyToManyField(minion, verbose_name=u'运行主机')
    
    def __unicode__(self):
        return self.type_name

class TicketTasks(models.Model):
    tasks_id = models.CharField(max_length=128, verbose_name=u"工单ID")
    title = models.CharField(max_length=512, verbose_name=u"工单标题")
    ticket_type = models.ForeignKey(TicketType, verbose_name=u"工单类型")
    creator = models.CharField(max_length=128, verbose_name=u"工单创建人")
    content =  models.CharField(max_length=4096, verbose_name=u"工单内容")
    create_time = models.DateTimeField(default= timezone.now, verbose_name=u"工单创建时间")
    modify_time = models.DateTimeField(auto_now=True, verbose_name=u"工单修改时间")
    handler = models.ForeignKey(User, verbose_name=u"工单处理人")
    state = models.IntegerField(choices=TICKET_STATE, blank=True, null=True, verbose_name=u"工单状态")

    def __unicode__(self):
        return self.tasks_id

class TicketOperating(models.Model):
    operating_id = models.ForeignKey(TicketTasks, verbose_name=u"工单ID")
    handler = models.ForeignKey(User, verbose_name=u"工单处理人")
    create_time = models.DateTimeField(default= timezone.now, verbose_name=u"工单操作时间")
    modify_time = models.DateTimeField(auto_now=True, verbose_name=u"工单修改时间")
    content =  models.CharField(max_length=4096, verbose_name=u"工单回复内容")
    result = models.IntegerField(choices=TICKET_RESULT, blank=True, null=True, verbose_name=u"工单结果")

    #def __unicode__(self):
    #    return self.operating_id





