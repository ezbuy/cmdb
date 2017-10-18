# coding: utf-8

from django.db import models
from asset.models import ASSET_ENV
# Create your models here.

class salt_module(models.Model):
    state_module = models.CharField(max_length=128)
    def __unicode__(self):
        return self.state_module

class webUrl(models.Model):
    host = models.CharField(max_length=64)
    url = models.CharField(max_length=64)
    ip = models.GenericIPAddressField()
    def __unicode__(self):
        return self.url

class webSite(models.Model):
    webSite = models.CharField(max_length=64)
    lb_server = models.CharField(max_length=64)
    state_module = models.ManyToManyField(salt_module)
    salt_pillar_host = models.CharField(max_length=64)
    svn_path = models.CharField(max_length=128)
    checkUrl = models.ManyToManyField(webUrl)
    svn_username = models.CharField(max_length=128)
    svn_password = models.CharField(max_length=128)
    svn_repo = models.CharField(max_length=128)
    recycle_cmd = models.CharField(max_length=128)
    env = models.IntegerField(choices=ASSET_ENV,verbose_name=u"运行环境")


    def __unicode__(self):
        return self.webSite

class groupName(models.Model):
    group_name = models.CharField(max_length=64)
    member = models.ManyToManyField(webSite)

    def __unicode__(self):
        return self.group_name