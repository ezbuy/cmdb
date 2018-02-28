# -*- coding: utf-8 -*-
# pylint: disable=print-statement

from __future__ import unicode_literals

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from asset.utils import deny_resubmit
from pydisque.client import Client
from mico.settings import disque_aws, disque_qcd
import json
# Create your views here.


disqueAWS = Client(disque_aws)
disqueAWS.connect()

disqueQCD = Client(disque_qcd)
disqueQCD.connect()


clientEnvMap = {
    'aws': disqueAWS,
    'qcd': disqueQCD
}


def index(request):
    return HttpResponse("hello django")


@login_required
@deny_resubmit(page_key='ack_job')
def ack_job(request):
    if not request.Post.keys():
        return HttpResponseRedirect('/')
    env = request.Post['env']
    jobIds = request.Post.getlist('jobIds')
    if len(jobIds) == 0:
        return HttpResponse('empty jobIds')
    if not (env in clientEnvMap.keys()):
        return HttpResponse('unknow disque env')
    try:
        client = clientEnvMap[env]
        client.ack_job(jobIds)
    except Exception as e:
        print e
        return HttpResponse(e)
    return HttpResponse("ok")


@login_required
@deny_resubmit(page_key='add_job')
def add_job(request):
    if not request.Post.keys():
        return HttpResponseRedirect('/')
    env = request.Post['env']
    queue = request.Post['queue']
    jobs = request.Post.getlist['jobs']
    ms_timeout = request.Post['timeout']
    replicate = request.Post['replicate']
    retry_sec = request.Post['retry']
    delay_sec = request.Post['delay']
    ttl_sec = request.Post['ttl']
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
