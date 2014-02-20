# -*- coding: utf-8 -*-

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from django.contrib import auth
from models import *
import os
import uuid
import BeautifulSoup
import time

def index(request):
    return render_to_response('index.html', locals())

def collect(request):
    urls = request.REQUEST.get("urls", "")
    repeat = request.REQUEST.get("repeat", "")
    for line in urls.split("\n"):
        try:
            print line
            line = line.strip()
            if not line:
                continue
            items = (line + ",,,").split(",")
            url = items[0]
            name = items[1]
            tag = items[2]

            if Product.objects.filter(url=url):
                pd = Product.objects.filter(url=url)[0]
                pd.name = name
                pd.tag = tag
                pd.save()
            else:
                pd = Product()
                pd.url = url
                pd.name = name
                pd.tag = tag
                pd.save()

            collect_url = pd.collect_url()
            break_flag = False
            for page_num in range(1,6):
                if break_flag:
                    break

                link = collect_url[:-1] + str(page_num)
                print link

                p = urllib2.urlopen(link).read()
                i = p.find('{html:"') + 7
                j = p.find('",type:"list"}')
                p = p[i:j].replace(r'\"', r'"')
                soup = BeautifulSoup.BeautifulSoup(p)
                tbody = soup.find("tbody")
                trs = tbody.findAll("tr")
                for tr in trs:
                    if not tr.find("td", "tb-buyer"):
                        continue

                    user = tr.find("td", "tb-buyer").getText()
                    price = float(tr.find("em", "tb-rmb-num").getText())
                    quantity = int(tr.find("td", "tb-amount").getText())
                    stime = tr.find("td", "tb-start").getText()

                    if Sale.objects.filter(product=pd).filter(user=user).filter(time=stime):
                        break_flag = True
                        break
                    else:
                        s = Sale()
                        s.product = pd
                        s.user = user
                        s.price = price
                        s.quantity = quantity
                        s.time = stime
                        s.save()

        except:
            print "quit:", line

    if repeat:
        current_url = request.get_full_path()
        time.sleep(int(repeat) * 60)
        print "repeat"
        rp = HttpResponseRedirect(current_url)
        rp.set_cookie("urls", urls.encode("utf8"), 3600*24*30)
        return rp

    rp = HttpResponseRedirect("/view")
    rp.set_cookie("urls", urls.encode("utf8"), 3600*24*30)
    return rp



def view(request):
    submit = request.REQUEST.get("submit")
    tags = request.REQUEST.get("tags", "")
    times = request.REQUEST.get("times", "")
    if submit:
        if times:
            start, end = times.split("/")
        else:
            start, end = None, None

        ts = tags.split()
        pds = Product.objects.all()
        for tag in ts:
            pds = pds.filter(tag__icontains=tag)

        total_sum = [0, 0, 0]
        for pd in pds:
            pd.data = pd.get_data(start, end)
            total_sum[0] += pd.data[0]
            total_sum[1] += pd.data[1]
            total_sum[2] += pd.data[2]

    return render_to_response('view.html', locals())




def product(request):
    submit = request.REQUEST.get("submit")
    name = request.REQUEST.get("name", "")
    if submit:
        pd = Product.objects.filter(name=name)
        if not pd:
            pd = Product.objects.filter(name__icontains=name)
        if not pd:
            pd = Product.objects.filter(url=name)
        if pd:
            pd = pd[0]
            sales = pd.get_sales()

    return render_to_response('product.html', locals())


