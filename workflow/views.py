from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from asset.utils import deny_resubmit

# Create your views here.
@login_required
@deny_resubmit(page_key='workflow_index')
def index(request):
    return render(request,'workflow_index.html')