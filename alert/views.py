import json
import time
from datetime import datetime
from functools import wraps

import requests
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, HttpResponse

from mico.settings import graphite_api, aac_api, aac_headers
from logs.models import goLog as GoLog


# Create your views here.
@login_required
def search_user(request):
    try:
        query = str(request.GET.get('query'))
    except:
        data = dict(errcode=400, errmsg='Missing required parameter "query"')
        return HttpResponse(json.dumps(data))

    users = User.objects.filter(Q(username__istartswith=query) | Q(userprofile__phone_number__istartswith=query))
    users_list = [
        dict(id=user.userprofile.phone_number, text=user.username + '(' + user.userprofile.phone_number + ')')
        for user in users if hasattr(user, 'userprofile')
    ]
    return HttpResponse(json.dumps(dict(users=users_list)))


def check_metrics(query):
    """Check metric is valid or not.

    :param str query: metric
    :return: bool
    """
    url = '%s/metrics/find/?query=%s' % (graphite_api, query)
    try:
        resp = requests.get(url)
        data = resp.json()
        for xxx in data:
            if xxx['leaf'] == 1 and xxx['id'] == query:
                return True
    except Exception as e:
        print e

    return False


@login_required
def find_metrics(request):
    try:
        query = str(request.GET.get('query'))
    except:
        data = dict(errcode=400, errmsg='Missing required parameter "query"')
        return HttpResponse(json.dumps(data))

    url = '%s/metrics/find/?format=completer&query=%s' % (graphite_api, query)
    try:
        resp = requests.get(url)
        metrics = resp.json()
        metrics = [dict(id=metric['path'], text=metric['path']) for metric in metrics['metrics']]
        data = dict(errcode=0, errmsg='ok', metrics=metrics)
    except Exception as e:
        print e
        data = dict(errcode=500, errmsg=str(e))

    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def search_metrics(request):
    try:
        query = str(request.GET.get('query'))
        page = request.GET.get('page') or '1'
        count = 50

        metrics = index_metrics()
        metrics = [{'id': metric, 'text': metric} for metric in metrics if query in metric]

        total_count = len(metrics)
        offset = (int(page) - 1) * count
        items = metrics[offset:offset+count]

        data = dict(items=items, total_count=total_count)
    except Exception as e:
        print e
        data = dict(items=[], total_count=0)

    return HttpResponse(json.dumps(data), content_type='application/json')


def cached_property(max_age=3600):
    _cached = {}

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if f not in _cached or (time.time() - _cached[f]['cached_time'] > max_age):
                data = f(*args, **kwargs)
                _cached[f] = {'data': data, 'cached_time': time.time()}

            return _cached[f]['data']

        return wrapper

    return decorator


@cached_property()
def index_metrics():
    url = '%s/metrics/index.json' % graphite_api
    try:
        resp = requests.get(url)
        metrics = resp.json()
    except Exception as e:
        print e
        metrics = []

    return metrics


def _phone_to_name(phone):
    try:
        user = User.objects.get(userprofile__phone_number=phone)
        return user.username
    except Exception as e:
        return ''


@login_required
def project_view(request):
    aac_url = '%s/projects' % aac_api
    try:
        resp = requests.get(aac_url, headers=aac_headers)
        data = resp.json()
        for project in data['projects']:
            try:
                phones = project['owner'].split(',')
                names = set([_phone_to_name(phone) for phone in phones])
                names.discard('')
                project['owner_name'] = ','.join(sorted(names))
            except Exception as e:
                del e
                project['owner_name'] = project['owner']
    except Exception as e:
        print e
        data = dict(errcode=500, errmsg=str(e), projects=[])

    return render(request, 'alert_project_index.html', data)


@login_required
def project_add(request):
    aac_url = '%s/projects' % aac_api
    try:
        resp = requests.post(aac_url, headers=aac_headers, data=request.POST)
        data = resp.json()
    except Exception as e:
        print e
        data = dict(errcode=500, errmsg=str(e))
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def project_edit(request):
    pid = request.GET.get('pid')

    aac_url = '%s/projects/%s' % (aac_api, pid)
    try:
        resp = requests.put(aac_url, headers=aac_headers, data=request.POST)
        data = resp.json()
    except Exception as e:
        print e
        data = dict(errcode=500, errmsg=str(e))
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def project_remove(request):
    if not request.user.is_superuser:
        data = dict(errcode=403, errmsg='Only SUPERUSER be able to delete.')
        return HttpResponse(json.dumps(data), content_type='application/json')

    pid = request.GET.get('pid')

    aac_url = '%s/projects/%s' % (aac_api, pid)
    try:
        resp = requests.delete(aac_url, headers=aac_headers)
        data = resp.json()
    except Exception as e:
        print e
        data = dict(errcode=500, errmsg=str(e))

    # Tracking user action
    ip = request.META['REMOTE_ADDR']
    action = 'delete project %s' % pid
    GoLog.objects.create(user=request.user, remote_ip=ip, goAction=action, result=data)

    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def item_view(request):
    pid = request.GET.get('pid')

    aac_url = '%s/items' % aac_api
    try:
        resp = requests.get(aac_url, headers=aac_headers, params=dict(pid=pid))
        data = resp.json()
        data['pid'] = pid
    except Exception as e:
        print e
        data = dict(errcode=500, errmsg=str(e), pid=pid, items=[])
    return render(request, 'alert_item_index.html', data)


@login_required
def item_add(request):
    aac_url = '%s/items' % aac_api
    try:
        keys = ('pid', 'name', 'ref', 'key', 'state', 'expr', 'interval', 'error', 'recovery', 'func', 'state_ratio',
                'silent_from', 'silent_to')
        data = {k: v for k, v in request.POST.items() if k in keys}
        if not check_metrics(data['key']):
            raise Exception('<strong>%s</strong> is NOT FOUND, please check and try again.' % data['key'])

        data['error'] = 'Status: ERROR\nMetric: %s\nValue: ' % (data['key'],)
        data['recovery'] = 'Status: OK\nMetric: %s\nValue: ' % (data['key'],)
        resp = requests.post(aac_url, headers=aac_headers, data=data)
        data = resp.json()
    except Exception as e:
        print e
        data = dict(errcode=500, errmsg=str(e))
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def item_edit(request):
    item_id = request.GET.get('item_id')

    aac_url = '%s/items/%s' % (aac_api, item_id)
    try:
        keys = ('pid', 'name', 'ref', 'key', 'state', 'expr', 'interval', 'error', 'recovery', 'func', 'state_ratio',
                'silent_from', 'silent_to')
        data = {k: v for k, v in request.POST.items() if k in keys}
        if not check_metrics(data['key']):
            raise Exception('<strong>%s</strong> is NOT FOUND, please check and try again.' % data['key'])

        data['error'] = 'Status: ERROR\nMetric: %s\nValue: ' % (data['key'],)
        data['recovery'] = 'Status: OK\nMetric: %s\nValue: ' % (data['key'],)
        resp = requests.put(aac_url, headers=aac_headers, data=data)
        data = resp.json()
    except Exception as e:
        print e
        data = dict(errcode=500, errmsg=str(e))
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def item_remove(request):
    if not request.user.is_superuser:
        data = dict(errcode=403, errmsg='Only SUPERUSER be able to delete.')
        return HttpResponse(json.dumps(data), content_type='application/json')

    item_id = request.GET.get('item_id')

    aac_url = '%s/items/%s' % (aac_api, item_id)
    try:
        resp = requests.delete(aac_url, headers=aac_headers)
        data = resp.json()
    except Exception as e:
        print e
        data = dict(errcode=500, errmsg=str(e))

    # Tracking user action
    ip = request.META['REMOTE_ADDR']
    action = 'delete item %s' % item_id
    GoLog.objects.create(user=request.user, remote_ip=ip, goAction=action, result=data)

    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def item_history(request):
    item_id = request.GET.get('item_id')

    aac_url = '%s/items/%s/history' % (aac_api, item_id)
    try:
        resp = requests.get(aac_url, headers=aac_headers)
        data = resp.json()

        body = ''
        for dx in data['data']:
            dt = datetime.fromtimestamp(int(dx['clock']))
            body += '<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (dt.strftime('%Y-%m-%d %H:%M:%S'),
                                                                    dx['value'],
                                                                    'OK' if dx['status'] == 0 else 'ERROR')
        data = dict(body=body)
    except Exception as e:
        print e
        # data = dict(errcode=500, errmsg=str(e))
        data = dict(body='')
    return HttpResponse(json.dumps(data), content_type='application/json')
