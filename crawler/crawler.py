# coding:utf-8

import os
import json
import urllib
import jieba as jb


class ThreadList(list):
    def find_comment_by_user(self, pat):
        return [com for th in self for com in th['comment'] if pat in com['user']]

    def get_img_link(self):
        """
        return a list (title, img_link)
        -> [0] : title
        -> [1] : list of img_link
        -> [2] : URL
        """
        return [{'title': th['title'], 'img_link': th['img_link'], 'id': j, 'url': th['url']}
                for j, th in enumerate(self)]
        # return [(th['title'], th['img_link'], th['url'] for th in self]


# scrapy crawl ptt -o beauty.json -a board=Beauty -a  pages=3


class ToolBox:
    def __init__(self, board='Gossiping', pages=1, file='tmp.json', title_lim=[], jsonf=None):
        if not jsonf:
            os.chdir(os.path.split(os.path.realpath(__file__))[0])
            com = 'scrapy crawl ptt '
            com += '-o %s ' % (file)
            com += '-a pages=%d ' % (pages)
            com += '-a board=%s ' % (board)

            if title_lim:
                com += '-a title_lim="'
                for lim in title_lim:
                    com += "%s," % (str(lim))
                com += '" '
            print('Command: ' + com)
            os.system('rm -f %' % (file))
            os.system('%' % (com))
            os.chdir('..')
        else:
            file = jsonf

        self.data = ThreadList()
        self.load_json(file)

    def get_title(self):
        return [i['title'] for i in self.data]

    def load_json(self, file):
        """
        load_json(NAME)
        load json as name
        """
        with open(file, 'r') as f:
            self.data.extend(json.load(f))

    def save_json(self, file):
        """
        save_json(NAME)
        save json as NAME
        """
        with open(file, 'w', encoding='utf8') as f:
            json.dump(self.data, f)

    def download_image(self, name):
        """
        Download imgur pictures in ./pictures<pid>
        classified by folder
        """
        if not os.path.exists(name):
            os.mkdir(name)
        for num, th in enumerate(self.data.get_img_link()):
            dirr = name + '/' + th['title'].replace('/', '.')

            if not os.path.exists(dirr):
                os.mkdir(dirr)
            yield num+1, th['title']

            for i, link in enumerate(th['img_link']):
                link = link.replace('https', 'http')

                try:
                    urllib.request.urlretrieve(link, dirr + '/' + str(i + 1) + '.jpg')
                except:
                    print('Get image error: %s in %s' % (link, th['title']))


class ToolBoxTextAnalysis(ToolBox):
    def cut_text(self):
        """
        Use Jieba to cut text
        """
        jb.set_dictionary('./dict.txt.big')
        jb.load_userdict('./ptt_custom.dict')
        res = []
        for ar in self.data:
            res.append([i for i in jb.cut(ar['text'].strip('\n'), cut_all=True)
                        if not i.isspace()])

        self.cut_res_text = res
        return res

    def cut_comment_text(self):
        """
        Use Jieba to cut comment
        """
        res = []
        for ar in self.data:
            for com in ar['comment']:
                res.append([i for i in jb.cut(com['text'].strip(''))
                            if len(i) > 1])
        self.cut_res_com = res
        return res

    def get_text_freq_sorted(self):
        """
        return dict to distribute cut result.
        if you don't call cut_text() before, get_freq_sorted() will be auto call cut_text() first.
        """
        try:
            self.cut_res_text
        except AttributeError:
            self.cut_text()

        dic = dict()
        for i in self.cut_res_text:
            for j in i:
                dic[j] = 1 if j not in dic else dic[j] + 1
        return sorted(dic.items(), key=lambda kv: kv[1], reverse=True)

    def get_comment_freq_sorted(self):
        try:
            self.cut_res_com
        except AttributeError:
            self.cut_comment_text()

        dic = dict()
        for i in self.cut_res_com:
            for j in i:
                dic[j] = 1 if j not in dic else dic[j] + 1
        return sorted(dic.items(), key=lambda kv: kv[1], reverse=True)


if __name__ == '__main__':
    a = ToolBoxTextAnalysis(json='beauty.json')
    # a = ToolBoxTextAnalysis(board='Gossiping', pages=2, file='gossip.json', title_lim=['-', '公告'])
    # a = ToolBoxTextAnalysis(board='Baseball', pages=2, file='baseball.json', title_lim=['-', '公告'])
    # a = ToolBoxTextAnalysis(board='Beauty', pages=2, file='beauty.json', title_lim=['-', '公告', '帥哥'])
    for i in a.download_image():
        print(i)
    # for i in a.get_freq_sorted():
    #    print(i)
    # a = ToolBox(json='tmp.json')
