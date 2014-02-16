# -*- coding: utf-8 -*-

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from django.contrib import auth
from models import *
import os
import uuid

def index(request):
    return render_to_response('index.html', locals())

def collect(request):
    urls = request.REQUEST("urls", "")
    for line in urls.split("\n"):
        print line
        line = line.strip()
        if not line:
            continue
        items = line + ",,,".split(",")
        url = items[0]
        name = items[1]
        tag = items[2]
        p = Product()
        p.url = url
        p.name = name
        p.tag = tag





def view(request):
    return render_to_response('view.html', locals())


