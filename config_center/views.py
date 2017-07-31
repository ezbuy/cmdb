from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render

from asset.models import gogroup
from asset.utils import goServicesni
from config_center.models import SVCResources, Resources


# Create your views here.
@login_required
def service_list(request):
    project_name = request.GET.get('projectName')
    go = goServicesni(project_name)
    group_name = gogroup.objects.all()
    services_list = go.getServiceName()
    paginator = Paginator(services_list, 20)
    page = request.GET.get('page')

    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        contacts = paginator.page(1)
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)

    q = SVCResources.objects.filter(svc__name=project_name).all()

    return render(request, 'service_list.html',
                  dict(project=contacts, groupName=group_name, project_name=project_name, svc_res=q))


@login_required
def resource_list(request):
    res_name = request.GET.get('res_name')
    res_obj = Resources.objects.filter(name=res_name).first()
    res_list = Resources.objects.all()

    q = SVCResources.objects.filter(res__name=res_name).all()

    return render(request, 'resource_list.html',
                  dict(res_list=res_list, res_obj=res_obj, svc_res=q))
