import json

import requests
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponse

from mico.settings import graphite_api, aac_api, aac_headers


# Create your views here.
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
def project_view(request):
    aac_url = '%s/projects' % aac_api
    try:
        resp = requests.get(aac_url, headers=aac_headers)
        data = resp.json()
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
