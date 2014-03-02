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
import csv
import xlwt


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


            nowtime = time.strftime('%Y-%m-%d %H:%M')

            req = urllib2.Request(url)
            req.add_header('Referer', 'http://www.taobao.com/')
            p = urllib2.urlopen(req).read()

            link = re.findall(r'"apiItemViews": "(.*?)",', p)[0]
            p2 = urllib2.urlopen(link).read()
            viewcount = int(re.findall(r':(.*?)}', p2)[0])

            link = re.findall(r'"apiItemInfo":"(.*?)",', p)[0]
            p3 = urllib2.urlopen(link).read()
            quanity = int(re.findall(r'quanity:(.*?),', p3)[0])
            confirm = int(re.findall(r'confirmGoods:(.*?),', p3)[0])

            print name, nowtime, viewcount, quanity, confirm

            info = Info()
            info.product = pd
            info.time = nowtime
            info.viewcount = viewcount
            info.quanity = quanity
            info.confirm = confirm
            info.save()

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
        print "waiting..."
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




def info(request):
    submit = request.REQUEST.get("submit")
    tags = request.REQUEST.get("tags", "")
    if submit:
        ts = tags.split()
        pds = Product.objects.all()
        for tag in ts:
            pds = pds.filter(tag__icontains=tag)

        infos = []
        for pd in pds:
            infos += list(Info.objects.filter(product=pd).order_by("time"))

    return render_to_response('info.html', locals())


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




def load_view(request):
    tags = request.REQUEST.get("tags", "")
    times = request.REQUEST.get("times", "")

    response = HttpResponse(mimetype='application/xls')
    response['Content-Disposition'] = 'attachment; filename=data.xls'

    workBook = xlwt.Workbook()

    if times:
        start, end = times.split("/")
    else:
        start, end = None, None

    ts = tags.split()
    pds = Product.objects.all()
    for tag in ts:
        pds = pds.filter(tag__icontains=tag)

    for pd in pds:
        sheet = workBook.add_sheet(pd.name + " ")

        sheet.write(0, 0, u'商品')
        sheet.write(0, 1, u'买家')
        sheet.write(0, 2, u'拍下价格')
        sheet.write(0, 3, u'数量')
        sheet.write(0, 4, u'付款时间')

        sales = pd.get_sales(start, end)
        for i in range(len(sales)):
            sale = sales[i]
            sheet.write(i+1, 0, sale.product.name)
            sheet.write(i+1, 1, sale.user)
            sheet.write(i+1, 2, str(sale.price))
            sheet.write(i+1, 3, str(sale.quantity))
            sheet.write(i+1, 4, sale.time)

    workBook.save(response)

    return response



def load_info(request):
    tags = request.REQUEST.get("tags", "")

    response = HttpResponse(mimetype='application/xls')
    response['Content-Disposition'] = 'attachment; filename=info.xls'

    workBook = xlwt.Workbook()

    ts = tags.split()
    pds = Product.objects.all()
    for tag in ts:
        pds = pds.filter(tag__icontains=tag)

    infos = []
    for pd in pds:

        sheet = workBook.add_sheet(pd.name + " ")

        sheet.write(0, 0, u'地址')
        sheet.write(0, 1, u'别名')
        sheet.write(0, 2, u'标签')
        sheet.write(0, 3, u'时间')
        sheet.write(0, 4, u'浏览量')
        sheet.write(0, 5, u'售出')
        sheet.write(0, 6, u'交易成功')

        infos = Info.objects.filter(product=pd).order_by("time")
        for i in range(len(infos)):
            info = infos[i]
            sheet.write(i+1, 0, info.product.url)
            sheet.write(i+1, 1, info.product.name)
            sheet.write(i+1, 2, info.product.tag)
            sheet.write(i+1, 3, info.time)
            sheet.write(i+1, 4, str(info.viewcount))
            sheet.write(i+1, 5, str(info.quanity))
            sheet.write(i+1, 6, str(info.confirm))

    workBook.save(response)

    return response


