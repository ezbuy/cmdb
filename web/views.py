from django.shortcuts import render,render_to_response,HttpResponseRedirect,HttpResponse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
# Create your views here.

def login(request):
    print request.method
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username = username,password = password)
        if user is not None:
            auth.login(request,user)
            return HttpResponseRedirect('/')
        else:
            return render(request,'login.html',{'login_err':'Wrong username or password!'})

    else:
        return render(request,'login.html')

@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/login/')