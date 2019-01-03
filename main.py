# coding:utf-8
from flask import Flask, flash, render_template, request, redirect, url_for, send_from_directory, Response
from flask_bootstrap import Bootstrap
from flask_markdown import markdown
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from werkzeug.utils import secure_filename

import time
import os
import random
import tarfile

from crawler.crawler import ToolBox, ThreadList


app = Flask(__name__)
markdown(app)
bootstrap = Bootstrap(app)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = "tmp"
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 16MB


nav = Nav()

@nav.navigation()
def mynavbar():
    return Navbar(
        'Ptt 圖片爬取器',
        View('Home', 'index'),
        View('圖片模式', 'page_mode'),
        View('關於我', 'aboutme')
    )


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
            return redirect(url_for('page_mode'))
        if 'btn_pid_mode' in request.form.keys():
            return redirect(url_for('pid_mode'))
        if 'btn_upload_json' in request.form.keys():
            return redirect(url_for('upload_json'))
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


@app.route('/upload_json', methods=['POST', 'GET'])
def upload_json():
    def allowed_file(filename):
        """
        :param filename: file name
        :return: 1 if type is leagal.
        check by ALLOWED_EXTENSIONS
        """
        ALLOWED_EXTENSIONS = set(['json'])
        return '.' in filename and \
               filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

    if 'upload' in request.form.keys() and request.method == 'POST':     # click btn-upload
        file = request.files['file']        # get file
        if file and allowed_file(file.filename):    # check file
            pid = str(random.randint(0, 100000))    # set pid
            filename = 'ori.json'                   # get a random file name
            upload_folder = app.config['UPLOAD_FOLDER'] + "/" + pid   # set upload folder
            os.mkdir(upload_folder)   # mkdir
            file.save(os.path.join(upload_folder, filename))          # save file
            return redirect(url_for('show_image1', pid=pid))
        else:
            flash("檔案名稱錯誤(非 json 檔案)", 'danger')
            return render_template('upload_json.html')
    else:
        return render_template('upload_json.html')


@app.route('/pid_mode', methods=['POST', 'GET'])
def pid_mode():
    if 'goto_pid' in request.form.keys():
        return redirect(url_for('show_image1', pid=request.form['pid']))
    else:
        return render_template('pid_mode.html')


@app.route('/show_image1/<pid>', methods=['GET', 'POST'])
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
    app.run(debug=True)
    # app.run()
