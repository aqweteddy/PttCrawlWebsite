# coding:utf-8
from flask import Flask, flash, render_template, request, redirect, url_for, send_from_directory, Response
from flask_bootstrap import Bootstrap
from flask_markdown import markdown
from crawler.crawler import ToolBox, ThreadList
import random
import tarfile
import time
import os
from flask_nav import Nav
from flask_nav.elements import Navbar, View



app = Flask(__name__)
markdown(app)
bootstrap = Bootstrap(app)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'



nav = Nav()

@nav.navigation()
def mynavbar():
    return Navbar(
        'Ptt 圖片爬取器',
        View('Home', 'index'),
        View('圖片模式', 'page_mode'),
        View('關於我', 'aboutme')
    )

# ...

nav.init_app(app)

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
@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        PID = random.randint(0, 100000)
        if 'btn_page_mode' in request.form.keys():
            # return redirect(url_for('page_mode', pid=str(PID)))
            return redirect(url_for('page_mode'))
    return render_template('index.html')


@app.route('/page_mode', methods=['POST', 'GET'])
def page_mode():
    pid = str(random.randint(0, 100000))
    folder = os.path.split(os.path.realpath(__file__))[0] + '/tmp/' + pid
    if request.method == 'POST':
        form = request.form
        if check_menu(form):
            lim = '+' + form['text_want'] if form['option'] == 'radio1' \
                else '-' + form['text_not_want']
            if lim == '+':
                lim = ''
            board = form['board'].strip()
            pages = int(form['pages'].strip())

            ToolBox(board=board, pages=pages, title_lim=lim.split(' '), file=folder + '/ori.json')
            return redirect(url_for('show_image1', pid=pid))

    return render_template('page_mode.html', pid=pid)
    # return render_template('page_mode.html')


@app.route('/show_image1/<pid>', methods=['GET', 'POST'])
@app.route('/show_image1', methods=['GET', 'POST'])
def show_image1(pid=None):
    if not pid:
        return redirect(url_for('index'))

    folder = os.path.split(os.path.realpath(__file__))[0] + '/tmp/' + pid
    # tb = ToolBox(jsonf='%s/%s.json' % (cur, pid))
    tb = ToolBox(jsonf="%s/%s.json" % (folder, 'ori'))
    if request.method != 'POST':
        return render_template('show_image1.html', data=tb.data.get_data(), pid=pid)

    form = dict()
    for i in request.form.keys():
        if i.find('download') != -1:
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
    tb.save_json('%s/%s.json' % (folder, pid))

    if 'download_image' in request.form.keys():
        return redirect(url_for('download', pid=pid))

    elif 'download_json' in request.form.keys():
        return send_from_directory(folder, pid + '.json', as_attachment=True)


@app.route('/download', methods=['GET', 'POST'])
@app.route('/download/<pid>', methods=['GET', 'POST'])
def download(pid=None):
    if not pid:
        return redirect(url_for('index'))
    folder = os.path.split(os.path.realpath(__file__))[0] + '/tmp/' + pid

    if request.method != 'POST':
        return render_template('download.html', pid=pid)
    if 'start_download' in request.form.keys():
        return send_from_directory(folder, pid + '.tar.gz', as_attachment=True)
    elif 'json_download' in request.form.keys():
        return send_from_directory(folder, pid + '.json', as_attachment=True)
    elif 'prev_page' in request.form.keys():
        return redirect(url_for('show_image1', pid=pid))


@app.route('/progress/<pid>', methods=['GET', 'POST'])
def progress(pid):
    folder = os.path.split(os.path.realpath(__file__))[0] + '/tmp/' + pid
    tb = ToolBox(jsonf="%s/%s.json" % (folder, pid))

    def downloading():
        source_dir = '%s/pictures%s' % (folder, pid)
        output = '%s/%s.tar.gz' % (folder, pid)
        num = len(tb.data)
        i = 0
        for i, j in tb.download_image(source_dir):
            percent = int(i / (num + 2) * 100)
            yield 'data:' + str('%d' % (percent)) + '\n\n'
        yield 'data:' + str(int((i + 1) / (num + 2) * 100)) + '\n\n'
        with tarfile.open(output, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
        time.sleep(2)
        yield 'data:100\n\n'

    return Response(downloading(), mimetype='text/event-stream')

@app.route('/aboutme', methods=['GET'])
def aboutme():
    return render_template('aboutme.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    # http_server = WSGIServer(('', 5000), app)
    # http_server.serve_forever()
    # monkey.patch_all()
    # gunicorn -b 127.0.0.1:5000 -w 2 main:app --timeout 2000
    # app.run(debug=True)
    app.run()
