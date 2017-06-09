from django.shortcuts import render,render_to_response,HttpResponseRedirect,HttpResponse,redirect
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from web.models import userLogin
# Create your views here.

def login(request):
    ip = request.META['REMOTE_ADDR']
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username = username,password = password)
        if user is not None and user.is_active:
            auth.login(request,user)
            obj = userLogin.objects.create(username=username,remote_ip=ip)
            obj.save()
            if request.GET.get('next') != 'None' and request.GET.get('next') != '':
                return redirect(request.GET.get('next'))
            return HttpResponseRedirect('/')
        else:
            return render(request,'login.html',{'login_err':'Wrong username or password!'})

    else:
        return render(request,'login.html',{'next':request.GET.get('next')})

@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/login/')