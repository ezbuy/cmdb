from django.shortcuts import render,render_to_response,HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
# Create your views here.
from logs.models import goLog

@login_required
def logs(request):
    logs_list = goLog.objects.all().order_by('-datetime')
    paginator = Paginator(logs_list,20)
    page = request.GET.get('page')

    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        contacts = paginator.page(1)
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)

    return render(request,'logs/logs.html',{'logs':contacts})
