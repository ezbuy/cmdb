# -*- coding: utf-8 -*_
from __future__ import unicode_literals

from django.db import models
from asset.models import gogroup


# Create your models here.
CATEGORIES = (
    (u'db', u'db'),
    (u'ops', u'ops'),
)


class ResTypes(models.Model):
    name = models.CharField(max_length=32, default='mysql', verbose_name=u'资源类型')

    def __unicode__(self):
        return self.name


class Resources(models.Model):
    name = models.CharField(max_length=128, verbose_name=u'资源唯一标识')
    type = models.ForeignKey(ResTypes, verbose_name=u'资源类型')
    category = models.CharField(max_length=16, choices=CATEGORIES, verbose_name=u'所属类别')
    comment = models.CharField(max_length=256, default='', verbose_name=u'资源说明')

    def __unicode__(self):
        return self.name


class SVCResources(models.Model):
    svc = models.ForeignKey(gogroup)
    res = models.ForeignKey(Resources)
