# coding: utf-8


from django.db import models
from asset.models import minion,ASSET_ENV
# Create your models here.


class winconf(models.Model):
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)
    repo = models.CharField(max_length=128)
    localpath = models.CharField(max_length=64)
    env = models.IntegerField(choices=ASSET_ENV, blank=True, null=True, verbose_name=u"运行环境")
    servicename = models.CharField(max_length=32)
    hostname = models.ForeignKey(minion)
    tasklist_name = models.CharField(max_length=32)

    def __unicode__(self):
        return self.servicename