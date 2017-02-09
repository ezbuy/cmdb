from django.shortcuts import render,render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.timezone import now, timedelta
from django.db.models import Count
from asset.models import gogroup,Asset
from logs.models import goLog,publishLog
from web.models import userLogin
# Create your views here.
@login_required
def index(request):
    users = User.objects.count()
    projects =  gogroup.objects.count()
    start = now().date()
    end = start + timedelta(days=1)
    build_count = goLog.objects.filter(datetime__range=(start,end)).count()
    top_three = goLog.objects.filter(datetime__range=(start,end)).values('user').annotate(count=Count('user')).order_by('-count')[0:3]
    hosts_count = Asset.objects.all().count()
    user_login_time = userLogin.objects.all().order_by('-login_time')[0:5]
    publish_logs = publishLog.objects.filter(datetime__range=(start,end)).order_by('-datetime')

    return render(request,'dashboard.html',{'users':users,'projects':projects,
        'build_count':build_count,'top_three':top_three,'hosts_count':hosts_count,
        'user_login_time':user_login_time,'publish_logs':publish_logs})