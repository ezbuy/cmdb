from __future__ import unicode_literals

from django.db import models

# Create your models here.

class userLogin(models.Model):
    username = models.CharField(max_length=100)
    remote_ip = models.GenericIPAddressField()
    login_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.username