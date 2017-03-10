from django.shortcuts import render,HttpResponse
from django.contrib.auth.decorators import login_required
from utils import kettle_run
from asset.utils import deny_resubmit
from mico.settings import kettle_log_url


# Create your views here.

@login_required
@deny_resubmit(page_key='kettle')
def kettle_index(request):
	return render(request,'kettleIndex.html')


@login_required
@deny_resubmit(page_key='kettle')
def kettle_execute(request):
    cmd_type = request.POST['type']
    kettle_file = request.POST['file']
    kettle_log_file = request.POST['kettle_log_file']
    ip = request.META['REMOTE_ADDR']
    username = request.user
    return_date = kettle_run.delay(username,ip,cmd_type,kettle_file,kettle_log_file,request.POST['phone_number'])
    #print return_date
    result = [{'kettle':'The kettle is running,please check kettle log file(%s%s)!' % (kettle_log_url,kettle_log_file)}]
    return render(request,'getdata.html',{'result':result})

