# -*- coding: utf-8 -*-
# pylint: disable=print-statement

from __future__ import unicode_literals

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from asset.utils import deny_resubmit
from pydisque.client import Client
from mico.settings import disque_aws, disque_qcd
from enum import Enum

# Create your views here.


disque_env = Enum('disque_env', ('aws', 'qcd'))

disqueAWS = Client(disque_aws)
disqueAWS.connect()

disqueQCD = Client(disque_qcd)
disqueQCD.connect()


def index(request):
    return HttpResponse("hello django")


@login_required
@deny_resubmit(page_key='ack_job')
def ack_job(request):
    if not request.Post.keys():
        return HttpResponseRedirect('/')
    env = request.Post['env']
    jobIds = request.Post.getlist('jobIds')
    try:
        if env == disque_env.aws.name:
            disqueAWS.ack_job(jobIds)
        elif env == disque_env.qcd.name:
            disqueQCD.ack_job(jobIds)
        else:
            return HttpResponse('unknown disque env')
    except Exception as e:
        print e
        return HttpResponse(e)
    return HttpResponse("ok")


