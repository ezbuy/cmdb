# -*- coding: utf-8 -*-
# pylint: disable=print-statement

from __future__ import unicode_literals

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from pydisque.client import Client
from mico.settings import disque_aws, disque_qcd, disque_hsg
import json
from django.shortcuts import render
from asset.utils import logs, deny_resubmit
# Create your views here.


DISQUE_AWS = Client(disque_aws)
DISQUE_QCD = Client(disque_qcd)
DISQUE_HSG = Client(disque_hsg)

DISQUE_CLIENT_MAP = {
    'aws': DISQUE_AWS,
    'qcd': DISQUE_QCD,
    'hsg': DISQUE_HSG
}

DEFAULT_CONTENT_TYPE = 'application/json'


@login_required
@deny_resubmit(page_key='disque_ack_job')
def ackjob_index(request):
    return render(request, 'disque_ack_job.html')


@login_required
@deny_resubmit(page_key='disque_add_job')
def addjob_index(request):
    return render(request, 'disque_add_job.html')


@login_required
def ack_job(request):
    user = request.user
    ip = request.META['REMOTE_ADDR']
    env = request.POST['env']
    jobIds = request.POST.getlist('jobIds', [])
    if not user.groups.filter(name__in=['admin', 'dba', 'disque']).exists():
        logs(user, ip, 'ack job: %s , zone: %s' % (jobIds, env), 'permission denied')
        return HttpResponse(json.dumps({'errcode': 403}), content_type=DEFAULT_CONTENT_TYPE)

    if not (env in DISQUE_CLIENT_MAP.keys()):
        logs(user, ip, 'ack job: %s' % jobIds, 'unknown disque zone: %s' % env)
        return HttpResponse(json.dumps({'errcode': 400, 'msg': 'unknown disque zone:%s' % env}), content_type=DEFAULT_CONTENT_TYPE)

    if len(jobIds) == 0:
        logs(user, ip, 'ack job: zone-%s' % env, 'empty jobIds')
        return HttpResponse(json.dumps({'errcode': 400, 'msg': 'empty jobIds'}), content_type=DEFAULT_CONTENT_TYPE)
    jobIds = map(lambda x: x.encode('utf-8'), jobIds)
    print user, env, jobIds

    try:
        client = DISQUE_CLIENT_MAP[env]
        client.connect()
        client.ack_job(*jobIds)
    except Exception as e:
        print e
        logs(user, ip, 'ack job: %s , zone: %s' % (jobIds, env), str(e))
        return HttpResponse(json.dumps({'errcode': 400, 'msg': str(e)}), content_type=DEFAULT_CONTENT_TYPE)
    logs(user, ip, 'ack job: %s , zone: %s' % (jobIds, env), 'success')
    return HttpResponse(json.dumps({'errcode': 200}), content_type=DEFAULT_CONTENT_TYPE)


@login_required
def add_job(request):
    user = request.user
    ip = request.META['REMOTE_ADDR']
    env = request.POST['env']
    queue = request.POST['queue_name']
    # timeout_ms = request.POST['timeout_ms']
    # replicate = request.POST['replicate']
    # retry_sec = request.POST['retry_sec']
    # delay_sec = request.POST['delay_sec']
    # ttl_sec = request.POST['ttl_sec']
    jobs = request.POST.getlist('jobs', [])
    # print user, env, queue, timeout_ms, replicate, retry_sec, delay_sec, ttl_sec
    print user, env, queue
    print jobs

    if not user.groups.filter(name__in=['admin', 'dba', 'disque']).exists():
        logs(user, ip, 'add job: %s - %s' % (env, queue), 'permission denied')
        return HttpResponse(json.dumps({'errcode': 403}), content_type=DEFAULT_CONTENT_TYPE)
    if not (env in DISQUE_CLIENT_MAP.keys()):
        logs(user, ip, 'add job: %s - %s' % (env, queue), 'unknown disque zone:%s' % env)
        return HttpResponse(json.dumps({'errcode': 400, 'msg': 'unknown disque zone:%s' % env}), content_type=DEFAULT_CONTENT_TYPE)
    if (not queue) or len(queue) == 0:
        logs(user, ip, 'add job: %s - %s' % (env, queue), 'empty queue name')
        return HttpResponse(json.dumps({'errcode': 400, 'msg': 'empty queue name'}), content_type=DEFAULT_CONTENT_TYPE)
    if len(jobs) == 0:
        logs(user, ip, 'add job: %s - %s' % (env, queue), 'empty jobs')
        return HttpResponse(json.dumps({'errcode': 400, 'msg': 'empty jobs'}), content_type=DEFAULT_CONTENT_TYPE)

    jobs = map(lambda x: x.encode('utf-8'), jobs)
    jobIds = []
    errJob = []
    client = DISQUE_CLIENT_MAP[env]
    client.connect()
    for job in jobs:
        try:
            print job
            jobId = client.add_job(queue, job)
            # jobId = client.add_job(queue, job, timeout=timeout_ms, replicate=replicate, delay=delay_sec, retry=retry_sec, ttl=ttl_sec)
            jobIds.append(jobId)
        except Exception as e:
            print e
            errJob.append(job)
    logs(user, ip, 'add job: %s - %s' % (env, queue), 'success')
    return HttpResponse(json.dumps({'errcode': 200, 'jobIds': jobIds, 'failJobs': errJob}), content_type=DEFAULT_CONTENT_TYPE)
