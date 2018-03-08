# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.


class ClusterInfo(models.Model):
    name = models.CharField(max_length=32, verbose_name=u"disque cluster alias name")
    addr = models.TextField(blank=True, null=True, default='', verbose_name=u"cluster address")

    def __unicode__(self):
        return self.name
