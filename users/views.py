# coding: utf-8

from django.shortcuts import render,render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User,Group
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from asset.models import UserProfile
from asset.utils import deny_resubmit
from django.forms import ModelForm



# Create your views here.

@login_required
def user_list(request):
    users_list = User.objects.all()
    paginator = Paginator(users_list,10)
    page = request.GET.get('page')

    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        contacts = paginator.page(1)
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)

    return render(request,'user_list.html',{'user_list':contacts})

@login_required
@deny_resubmit(page_key='add_user')
def user_add_html(request):
    groups = Group.objects.all()
    return  render(request,'user_add.html',{'groups':groups})

@login_required
@deny_resubmit(page_key='add_user')
def user_add(request):
    try:
        name = request.POST.get('name')
        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        group_id = request.POST.getlist('group_id')
        phone = request.POST.get('phone')
        info = User.objects.create_user(username=name,password=password,last_name=full_name)
        UserProfile.objects.create(phone_number=phone, user=info)
        for id in group_id:
            info.groups.add(id)
        print '-------%s--%s-------%s--%s' % (name,full_name,group_id,phone)
        result = [{'add_user':'successful'}]
    except Exception, e:
        print e
        result = [{'add_user': 'failed'}]
    return render(request,'getdata.html',{'result':result})

class user_edit_form(ModelForm):
    class Meta:
        model = User
        fields = ["username","first_name"]

@login_required
def user_edit(request, id):
    user_info = User.objects.get(id=id)
    print '-----user_info---',user_info
    if request.method == 'GET':
        groups = Group.objects.all()
        return render(request,'user_edit.html',{'user_info':user_info,'groups':groups})
    elif request.method == 'POST':
        try:
            name = request.POST.get('name')
            full_name = request.POST.get('full_name')
            password = request.POST.get('password')
            group_id = request.POST.getlist('group_id')
            phone = request.POST.get('phone')

            print '-------%s--%s-------%s--%s' % (name,full_name,group_id,phone)
            user_info.username = name
            user_info.first_name = full_name
            phone_obj = UserProfile.objects.get(user=user_info)
            phone_obj.phone_number = phone
            phone_obj.save()
            if password != '':
                user_info.set_password(password)

            for id in group_id:
                user_info.groups.add(int(id))
            for info in user_info.groups.all():
                if str(info.id) not in group_id:
                    user_info.groups.remove(info.id)
            user_info.save()
            result = [{'user_update': 'successful'}]
        except Exception, e:
            print e
            result = [{'user_update': 'failed'}]
        return render(request, 'getdata.html', {'result': result})




