from flask import Flask, flash, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from crawler.crawler import ToolBox, ThreadList
import random
import zipfile as zip


app = Flask(__name__)
bootstrap = Bootstrap(app)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'


def check_menu(form):
    if form['option'] == 'radio1' and form['text_not_want'].strip() == '':
        flash('請輸入不想要的標題內容', 'danger')
        return False
    if form['option'] == 'radio2' and form['text_want'].strip() == '':
        flash('請輸入想要的標題內容', 'danger')
        return False
    if form['board'].strip() == '':
        flash('請輸入看板名稱', 'danger')
        return False
    if form['pages'].strip() == '':
        flash('請輸入頁數', 'danger')
        return False
    return True


@app.route('/', methods=['GET', 'POST'])
def index():
    global PID
    PID = random.randint(0, 100000)
    return redirect(url_for('page_mode', pid=PID))
    # return redirect(url_for('page_mode', ))


@app.route('/page_mode/<pid>', methods=['POST', 'GET'])
def page_mode(pid=None):
    if request.method == 'POST':
        form = request.form
        if check_menu(form):
            lim = '+' + form['text_want'] if form['option'] == 'radio1' \
                else '-' + form['text_not_want']
            if lim == '+':
                lim = ''
            board = form['board'].strip()
            pages = int(form['pages'].strip())

            ToolBox(board=board, pages=pages, title_lim=lim.split(' '), file=str(pid) + '.json')
            print('----------------------------')
            return redirect(url_for('show_image1', pid=pid))

    return render_template('page_mode.html', pid=pid)
    # return render_template('page_mode.html')


@app.route('/show_image1/<pid>', methods=['GET', 'POST'])
def show_image1(pid):
    # tb = ToolBox(json='%s.json' % (pid))

    if request.method != 'POST':
       # return render_template('show_image1.html', data=tb.data.get_img_link(), pid=pid)

        tb = ToolBox(json='97608.json')
        tmp = []
        for i, th in enumerate(tb.data):
            tmp.append(dict(title=th['title'], img_link=th['img_link'], id=i, url=th['url']))
        return render_template('show_image1.html', data=tmp)

    form = dict()
    for i in request.form.keys():
        if i == 'download':
            continue
        a = int(i.split('_')[1])
        b = int(i.split('_')[-1])
        if a in form.keys():
            form[a].append(b)
        else:
            form[a] = [b]

    tmp_data = []
    for a, b in form.items():
        tmp_data.append(tb.data[a].copy())
        tmp_data[-1]['img_link'] = []
        for i in b:
            tmp_data[-1]['img_link'].append(tb.data[a]['img_link'][i])
    tb.data = ThreadList(tmp_data.copy())

    for i, j in tb.download_image(str(pid)):
        print(i, j)


if __name__ == '__main__':
    # http_server = WSGIServer(('', 5000), app)
    # http_server.serve_forever()
    # monkey.patch_all()
    app.run()
