# coding: utf-8

from django.db import models
from asset.models import minion,ASSET_ENV
# Create your models here.


class memcache(models.Model):
    saltMinion = models.ForeignKey(minion)
    env = models.IntegerField(choices=ASSET_ENV, blank=True, null=True, verbose_name=u"运行环境")
    ip = models.GenericIPAddressField()
    port = models.CharField(max_length=32,default="11211")
    memcacheName = models.CharField(max_length=64,unique=True)

    def __unicode__(self):
        return self.memcacheName



