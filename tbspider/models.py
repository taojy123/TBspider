# -*- coding: utf-8 -*-

from django.db import models
import urllib2
import re

class Product(models.Model):
    url = models.CharField(max_length=255, blank=True , null=True)
    name = models.CharField(max_length=255, blank=True , null=True)
    tag = models.CharField(max_length=255, blank=True , null=True)
    item_id = models.CharField(max_length=255, blank=True , null=True)
    seller_num_id = models.CharField(max_length=255, blank=True , null=True)
    sbn = models.CharField(max_length=255, blank=True , null=True)

    def collect_url(self):
        if self.item_id and self.seller_num_id and self.sbn:
            item_id = self.item_id
            seller_num_id = self.seller_num_id
            sbn = self.sbn
        else:
            request = urllib2.Request(self.url)
            request.add_header('Referer', 'http://www.taobao.com/')
            p = urllib2.urlopen(request).read()

            item_id = re.findall(r'itemId:"(.*?)",', p)[0]
            seller_num_id = re.findall(r'sellerId:"(.*?)",', p)[0]
            sbn = re.findall(r'&sbn=(.*?)&', p)[0]

            self.item_id = item_id
            self.seller_num_id = seller_num_id
            self.sbn = sbn
            self.save()

        collect_url = "http://detailskip.taobao.com/json/show_buyer_list.htm?item_id=%s&seller_num_id=%s&sbn=%s&callback=Hub.data.records_reload&page_size=15&bidPage=1"%(item_id, seller_num_id, sbn)
        return collect_url




class Sale(models.Model):
    product = models.ForeignKey(Product)
    user = models.CharField(max_length=255, blank=True , null=True)
    price = models.FloatField(default=0)
    quantity = models.IntegerField(default=0)
    time = models.CharField(max_length=255, blank=True , null=True)
