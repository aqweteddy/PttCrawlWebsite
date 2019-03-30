# coding:utf-8

import scrapy
from scrapy.selector import Selector
from ptt_crawl.items import PttCrawlItem
from datetime import datetime


def filter(limits, text):
    if limits == []:
        return True
    if limits[0] == '+':
        for lim in limits[1:]:
            if lim in text:
                return True
        return False
    else:  # -
        for lim in limits[1:]:
            if lim in text:
                return False
        return True


class PttSpiderByPage(scrapy.Spider):
    name = 'ptt_url'
    allowed_domains = ['ptt.cc']
    now_pages = 0

    def __init__(self, *args, **kwargs):
        super(PttSpiderByPage, self).__init__(*args, **kwargs)
        self.item = PttCrawlItem()
        self.title_lim = []

        self.start_urls = ['https://www.ptt.cc/bbs/%s/index.html' %
                           (kwargs['board'])] if 'board' in kwargs.keys() else []
        self.title_lim = kwargs['title_lim'].split(
            ',')[0:-1] if 'title_lim' in kwargs.keys() else []
        self.MAX_PAGES = int(
            kwargs['pages']) if 'pages' in kwargs.keys() else 1

    def start_requests(self):
        yield scrapy.Request(self.start_urls[0], cookies={'over18': '1'})

    def parse(self, resp):
        self.now_pages += 1
        print('Now at %s, page #%d' %
              (str(resp).split(' ')[1][:-2], self.now_pages))

        for arti in resp.xpath('//div[@class="r-ent"]/div[@class="title"]/a'):
            title = arti.xpath('text()').extract()[0]
            url = resp.urljoin(arti.xpath('@href').extract()[0])

            if filter(self.title_lim, title):
                # print('Parsing: %s\t%s' % (title, url))
                yield scrapy.Request(url=url, cookies={'over18': '1'}, callback=self.parse_post)
            else:
                print('Exclude: %s\t%s' % (title, url))

        if self.now_pages < self.MAX_PAGES:
            next_page = resp.xpath(
                '//div[@id="action-bar-container"]//a[contains(text(), "上頁")]/@href')
            if next_page:
                url = resp.urljoin(next_page[0].extract())
                yield scrapy.Request(url=url, cookies={'over18': '1'}, callback=self.parse)

    def parse_post(self, resp):
        try:
            tmp = resp.xpath(
                '//meta[@property="og:title"]/@content')[0].extract()
            self.item['title'] = tmp
        except IndexError:
            self.item['title'] = ""
        except:
            self.item['title'] = 'err'
        try:
            self.item['category'] = 'Re' if 'Re:' in tmp else tmp.split(']')[0][1:].strip()
        except IndexError:
            self.item['category'] = 'not found'
        except:
            self.item['category'] = 'err'
        self.item['text'] = resp.xpath(
            '//div[@id="main-content"]/text()')[0].extract()
        try:
            self.item['author'] = resp.xpath(
                '//div[@class="article-metaline"]/span[text()="作者"]/following-sibling::span[1]/text()')[0].extract()
        except IndexError:
            self.item['author'] = ""

        self.item['img_link'] = []
        for link in resp.xpath('//div[@id="main-content"]/a/@href'):
            tmp = link.extract()
            if '.jpg' in tmp.split('/')[-1] or '.png' in tmp.split('/')[-1] \
                    or '.gif' in tmp.split('/')[-1]:
                tmp.replace('https', 'http')
                self.item['img_link'].append(tmp)
            elif 'imgur' in tmp:
                tmp = 'http://i.imgur.com/' + link.extract().split('/')[-1]
                if '.jpg' not in tmp:
                    tmp += '.jpg'
                tmp.replace('https', 'http')
                self.item['img_link'].append(tmp)
        self.item['url'] = resp.url
        print('Parsed: %s\t%s' % (self.item['title'], resp.url))

        yield self.item
