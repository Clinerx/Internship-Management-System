from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def index(request):
    return render(request, 'index.html')

def admin_2(request):
    return render(request, 'admin2.html')