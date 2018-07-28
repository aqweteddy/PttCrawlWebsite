# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class PttCrawlItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    category = scrapy.Field()
    author = scrapy.Field()
    date = scrapy.Field()
    text = scrapy.Field()
    comment = scrapy.Field()
    url = scrapy.Field()
    ip_author = scrapy.Field()
    img_link = scrapy.Field()
    