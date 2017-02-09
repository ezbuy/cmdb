from __future__ import unicode_literals

from django.db import models

# Create your models here.

class goLog(models.Model):
    user = models.CharField(max_length=100)
    remote_ip = models.GenericIPAddressField()
    goAction = models.TextField()
    result = models.TextField(default='')
    datetime = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.goAction

class publishLog(models.Model):
    user = models.CharField(max_length=100)
    remote_ip = models.GenericIPAddressField()
    publish_url = models.TextField(default='')
    publish_result = models.TextField(default='')
    datetime = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.publish_url
