# -*- coding: utf-8 -*-
import json
import re

import consul
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from asset.utils import logs, deny_resubmit
from mico.settings import CONSUL_AGENT


class KV(object):
    def __init__(self, host):
        """
        :param host: host of consul agent
        """
        self.c = consul.Consul(host=host)

    def get_keys(self):
        """Returns a list of keys excluded directory."""
        _, keys = self.c.kv.get('', keys=True)
        return [k for k in keys if not k.endswith('/')] if keys else []

    def get_value(self, key):
        _, val = self.c.kv.get(key)
        print val
        if isinstance(val, dict):
            val = val['Value']
        return val

    def set_value(self, key, val):
        self.c.kv.put(key, val)


@login_required
@deny_resubmit(page_key='consul_kv_req')
def consul_kv_index(request):
    return render(request, 'consulKVIndex.html')


@login_required
def consul_kv_req(request):
    user = request.user
    ip = request.META['REMOTE_ADDR']
    method = request.POST['method']  # get/set
    zone = request.POST['zone']  # hsg/aws/qcd
    key = request.POST['key']  # key of consul KV
    val = request.POST['val']  # val of consul KV

    print method, zone, key, val

    if not (method and zone and key):
        return HttpResponse(json.dumps({'errcode': 400}), content_type="application/json")

    kv = KV(CONSUL_AGENT[zone])
    data = {}
    if method.upper() == 'GET':
        logs(user, ip, 'Consul KV: query %s' % (zone,), key)

        key_exists = key in kv.get_keys()
        if not key_exists:
            data['exists'] = False
        else:
            # Developers cannot see secret or password.
            if re.search(r'passwd|password|secret', key, re.I) and \
                    not user.groups.filter(name__in=['admin', 'dba']).exists():
                val = '*' * 8
            else:
                val = kv.get_value(key)

            data['exists'] = True
            data['value'] = val

        data['errcode'] = 200

    elif method.upper() == 'SET':
        logs(user, ip, 'Consul KV: update %s' % (zone,), 'Key: %s\nVal: %s' % (key, val))

        if not user.groups.filter(name__in=['admin', 'dba']).exists():
            data['errcode'] = 403
        else:
            kv.set_value(key, val)
            data['errcode'] = 200

    return HttpResponse(json.dumps(data), content_type="application/json")
