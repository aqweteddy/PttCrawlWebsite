# coding:utf-8

"""
MAC OS X
python 3.6 conda.
IDE: pyCharm
code by KeddyPlz
"""

import os
import json
import urllib
import time


class ThreadList(list):
    """
    inherit from standard list
    """
    def find_comment_by_user(self, pat):
        """
        find user by comment pattern
        :param pat: pattern::string
        :return:  list of user's name
        """
        return [com for th in self for com in th['comment'] if pat in com['user']]

    def get_data(self):
        """
        return a list (title, img_link)
        -> [0] : title
        -> [1] : list of img_link
        -> [2] : URL
        -> [3] : text
        """
        return [{'title': th['title'], 'img_link': th['img_link'], 'id': j, 'url': th['url'], 'text': th.get('text', '0')}
                for j, th in enumerate(self)]

# scrapy crawl ptt -o beauty.json -a board=Beauty -a  pages=3


class ToolBox(ThreadList):
    def __init__(self, board='Gossiping', pages=1, file='tmp.json', title_lim=[], jsonf=None, copy_data=[], simple_mode=True):
        """
        construct a Class and crawl.
        :param board: crawled board
        :param pages: crawl page number.
        :param file: output .json file name
        :param title_lim: title limit.
        :param jsonf: construct by json file.
        """
        if copy_data:
            self.extend(copy_data)
            return
        os.chdir(os.path.split(os.path.realpath(__file__))[0])
        print(os.getcwd())
        com = 'scrapy crawl ptt ' if not simple_mode else 'scrapy crawl ptt_url '
        # output json file name
        com += '-o %s ' % (file)
        # page
        com += '-a pages=%d ' % (pages)
        # board
        com += '-a board=%s ' % (board)

        # title limit
        if title_lim:
            com += '-a title_lim="'
            for lim in title_lim:
                com += "%s," % (str(lim))
            com += '" '
        # not opened by json_file
        if not jsonf:
            # start crawl
            print('Command: ' + com)
            os.system('rm -f {}'.format(file))
            os.system('{}'.format(com))
        # opened by json file
        else:
            file = jsonf

        # all data save in self
        self.load_json(file)
        self.com = com
        self.file = file

    def update(self):
        """
        update crawled data
        :return: true if success
        """

        # crawl
        print('Command: ' + self.com)
        os.system('rm -f {}'.format(self.file))
        os.system('{}'.format(self.com))
        # combine
        old = self
        self.load_json(os.getcwd() + '/' + self.file)
        url = [i['url'] for i in self]

        print(url)
        for th in old:
            if not th['url'] in url:
                self.append(th)
        self.save_json(self.file)

    def get_title(self):
        """
        get all title in object.
        """
        return [i['title'] for i in self]

    def load_json(self, file):
        """
        load_json(NAME)
        load json as name
        """
        with open(file, 'r', encoding="utf8") as f:
            self.extend(json.load(f))

    def save_json(self, file):
        """
        save_json(NAME)
        save json as NAME
        """
        with open(file, 'w', encoding='utf8') as f:
            json.dump(self, f, ensure_ascii=False)

    def download_image(self, name):
        """
        classified by folder
        """
        if not os.path.exists(name):
            os.mkdir(name)
        for num, th in enumerate(self.get_data()):
            dirr = name + '/' + th['title'].replace('/', '.')

            if not os.path.exists(dirr):
                os.mkdir(dirr)

            yield num+1, th['title']
            for i, link in enumerate(th['img_link']):
                link = link.replace('https', 'http')
                try:
                    urllib.request.urlretrieve(
                        link, dirr + '/' + str(i + 1) + '.jpg')
                except:
                    print('Get image error: %s in %s' % (link, th['title']))


if __name__ == '__main__':
    # a = ToolBoxAnalyze(jsonf='tmp.json')
    # a = ToolBoxAnalyze(board='Gossiping', pages=10, title_lim=['-', '公告'])
    # a = ToolBoxTextAnalysis(board='Baseball', pages=2, file='baseball.json', title_lim=['-', '公告'])
    a = ToolBox(board='Beauty', pages=2, file='beauty.json', title_lim=['-', '公告', '帥哥'])
    time.sleep(5)
    a.update()

    # for i in a.download_image():
    #     print(i)
    # for i in a.get_freq_sorted():
    #    print(i)
    # a = ToolBox(json='tmp.json')
