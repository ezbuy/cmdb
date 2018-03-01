# -*- coding: utf-8 -*-
# pylint: disable=print-statement

from __future__ import unicode_literals

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from pydisque.client import Client
from mico.settings import disque_aws, disque_qcd
import json
from django.shortcuts import render
# Create your views here.


disqueAWS = Client(disque_aws)
disqueAWS.connect()

disqueQCD = Client(disque_qcd)
disqueQCD.connect()


clientEnvMap = {
    'aws': disqueAWS,
    'qcd': disqueQCD
}


def ackjob_index(request):
    return render(request, 'disque_ack_job.html')


def addjob_index(request):
    return render(request, 'disque_add_job.html')


default_content_type = 'application/json'


@login_required
def ack_job(request):
    env = request.POST['env']
    if not (env in clientEnvMap.keys()):
        return HttpResponse(json.dumps({'errcode': 400, 'msg': 'unknown disque zone:%s' % env}), content_type=default_content_type)
    jobIds = request.POST.getlist('jobIds[]', [])
    if len(jobIds) == 0:
        return HttpResponse(json.dumps({'errcode': 400, 'msg': 'empty jobIds'}), content_type=default_content_type)
    jobIds = map(lambda x: x.encode('utf-8'), jobIds)
    print env, jobIds
    try:
        client = clientEnvMap[env]
        client.ack_job(*jobIds)
    except Exception as e:
        print e
        return HttpResponse(json.dumps({'errcode': 400, 'msg': str(e)}), content_type=default_content_type)
    return HttpResponse(json.dumps({'errcode': 200}), content_type=default_content_type)


@login_required
def add_job(request):
    env = request.POST['env']
    queue = request.POST['queue']
    jobs = request.POST.getlist['jobs']
    ms_timeout = request.POST['timeout']
    replicate = request.POST['replicate']
    retry_sec = request.POST['retry']
    delay_sec = request.POST['delay']
    ttl_sec = request.POST['ttl']
    if not (env and queue):
        return HttpResponse('env or queue is empty')
    if len(jobs) == 0:
        return HttpResponse('empty jobs')

    if not (env in clientEnvMap.keys()):
        return HttpResponse('unknow disque env')
    client = clientEnvMap[env]
    jobIds = []
    errJob = []
    for job in jobs:
        try:
            jobId = client.add_job(queue, json.dumps(job), timeout=ms_timeout, replicate=replicate, delay=delay_sec, retry=retry_sec, ttl=ttl_sec)
            jobIds.append(jobId)
        except Exception as e:
            print e
            errJob.append(job)
    return HttpResponse(json.dumps({'jobIds': jobIds, 'failJobs': errJob}), content_type='application/json')
