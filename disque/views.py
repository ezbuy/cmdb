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

default_content_type = 'application/json'


@login_required
def ackjob_index(request):
    return render(request, 'disque_ack_job.html')


@login_required
def addjob_index(request):
    return render(request, 'disque_add_job.html')


@login_required
def ack_job(request):
    env = request.POST['env']
    if not (env in clientEnvMap.keys()):
        return HttpResponse(json.dumps({'errcode': 400, 'msg': 'unknown disque zone:%s' % env}), content_type=default_content_type)
    jobIds = request.POST.getlist('jobIds', [])
    if len(jobIds) == 0:
        return HttpResponse(json.dumps({'errcode': 400, 'msg': 'empty jobIds'}), content_type=default_content_type)
    jobIds = map(lambda x: x.encode('utf-8'), jobIds)
    print request.user, env, jobIds
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
    queue = request.POST['queue_name']
    timeout_ms = request.POST['timeout_ms']
    replicate = request.POST['replicate']
    retry_sec = request.POST['retry_sec']
    delay_sec = request.POST['delay_sec']
    ttl_sec = request.POST['ttl_sec']
    jobs = request.POST.getlist('jobs', [])
    print request.user, env, queue, timeout_ms, replicate, retry_sec, delay_sec, ttl_sec
    print jobs

    if not (env in clientEnvMap.keys()):
        return HttpResponse(json.dumps({'errcode': 400, 'msg': 'unknown disque zone:%s' % env}), content_type=default_content_type)
    if (not queue) or len(queue) == 0:
        return HttpResponse(json.dumps({'errcode': 400, 'msg': 'emtpy queue name'}), content_type=default_content_type)
    if len(jobs) == 0:
        return HttpResponse(json.dumps({'errcode': 400, 'msg': 'empty jobs'}), content_type=default_content_type)

    jobs = map(lambda x: x.encode('utf-8'), jobs)
    client = clientEnvMap[env]
    jobIds = []
    errJob = []
    for job in jobs:
        try:
            print job
            jobId = client.add_job(queue, job, timeout=timeout_ms, replicate=replicate, delay=delay_sec, retry=retry_sec, ttl=ttl_sec)
            jobIds.append(jobId)
        except Exception as e:
            print e
            errJob.append(job)
    return HttpResponse(json.dumps({'errcode': 200, 'jobIds': jobIds, 'failJobs': errJob}), content_type=default_content_type)
