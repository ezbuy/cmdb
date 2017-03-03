from django.shortcuts import render,HttpResponse
from django.contrib.auth.decorators import login_required
from utils import kettle_run

# Create your views here.

@login_required
def kettle_index(request):
	return render(request,'kettleIndex.html')


@login_required
def kettle_execute(request):
    cmd_type = request.GET['type']
    file_path = request.GET['file']
    ip = request.META['REMOTE_ADDR']
    username = request.user
    return_date = kettle_run.delay(cmd_type,file_path)
    print return_date
    result = [{'kettle':'The kettle is running,please check kettle log file!'}]
    return render(request,'getdata.html',{'result':result})

