# -*- coding:utf-8 -*-

from django.contrib.auth.models import Group
from django import template
import datetime
register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    try:
        group = Group.objects.get(name=group_name)
        return True if group in user.groups.all() else False

    except Exception, e:
        print e
        return False

@register.filter(name='print_timestamp')
def print_timestamp(timestamp):
    try:
        ts = float(timestamp)
    except ValueError:
        return None
    return datetime.datetime.fromtimestamp(ts)
