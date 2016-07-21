from django.shortcuts import render,render_to_response,HttpResponse

# Create your views here.
from www.utils import deployWww

def list(request):
        deployWww.delay('ezbuy.sg')
        return render_to_response('getText.html')