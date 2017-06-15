import json
import time
from functools import wraps

import requests
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, HttpResponse

from mico.settings import graphite_api, aac_api, aac_headers


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


@login_required
def project_view(request):
    aac_url = '%s/projects' % aac_api
    try:
        resp = requests.get(aac_url, headers=aac_headers)
        data = resp.json()
        for project in data['projects']:
            try:
                user = User.objects.get(userprofile__phone_number=project['owner'])
                project['owner_name'] = user.username
            except Exception as e:
                del e
                project['owner_name'] = project['owner']
    except Exception as e:
        print e
        data = dict(errcode=500, errmsg=str(e), projects=[])

    print data
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
        resp = requests.post(aac_url, headers=aac_headers, data=request.POST)
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
        resp = requests.put(aac_url, headers=aac_headers, data=request.POST)
        data = resp.json()
    except Exception as e:
        print e
        data = dict(errcode=500, errmsg=str(e))
    return HttpResponse(json.dumps(data), content_type='application/json')
