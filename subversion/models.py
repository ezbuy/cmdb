# coding: utf-8

from django.db import models
from asset.models import ASSET_ENV,minion
# Create your models here.

class subversion(models.Model):
    env = models.IntegerField(choices=ASSET_ENV, blank=True, null=True, verbose_name=u"运行环境")
    hostname = models.ForeignKey(minion)
    svnparentpath = models.CharField(max_length=32, blank=True, null=True, default='/srv/svn/')
    svnowner = models.CharField(max_length=32, blank=True, null=True, default='www-data:www-data')
    svnrooturl = models.CharField(max_length=32)
    svnusername = models.CharField(max_length=32)
    svnpassword =  models.CharField(max_length=32)
    svnpasswordfile = models.CharField(max_length=32)

    def __unicode__(self):
        return self.svnrooturl



