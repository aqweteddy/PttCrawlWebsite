# coding:utf-8


"""
MAC OS X
python 3.6 conda.
IDE: pyCharm
"""


from flask import Flask, flash, render_template, request, redirect, url_for, send_from_directory, Response
from flask_bootstrap import Bootstrap
import json

# from concurrent.futures import ThreadPoolExecutor

import time
import os
import random
import tarfile

from crawler.crawler import ToolBox, ThreadList

FOLDER = os.path.split(os.path.realpath(__file__))[0] + '/tmp'
# settings
app = Flask(__name__)
bootstrap = Bootstrap(app)
app.secret_key = 'ldjfkl3kljcik3k'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = "tmp"
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # Upload json length (5mb)


# home page
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # to page mode
        if 'btn_page_mode' in request.form.keys():
            return redirect(url_for('page_mode'))
        # to pid mode
        if 'btn_pid_mode' in request.form.keys():
            return redirect(url_for('pid_mode'))
        # to upload json mode
        if 'btn_upload_json' in request.form.keys():
            return redirect(url_for('upload_json'))
    return render_template('index.html')


# page mode
@app.route('/page_mode', methods=['POST', 'GET'])
def page_mode():
    def check_menu(form):
        # check input legal
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

    # get pid
    pid = str(random.randint(0, 100000))
    # get FOLDER
    if request.method == 'POST':
        form = request.form
        if check_menu(form):
            if form['option'] == 'radio1':
                lim = '- ' + form['text_not_want']
            elif form['option'] == 'radio2':
                lim = '+ ' + form['text_want']
            else:
                lim = '+ '
            simple_flag = True if form['option1'] == 'radio3' else False

            board = form['board'].strip()
            pages = int(form['pages'].strip())
            ToolBox(board=board, pages=pages, title_lim=lim.split(' '), file=FOLDER + '/' + str(pid) +'/ori.json', simple_mode=simple_flag)

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
        try:
            file = request.files['file']        # get file
        except KeyError:
            flash("沒有選擇檔案 或是檔案格式錯誤", 'danger')
            return render_template('upload_json.html')
        if file and allowed_file(file.filename):    # check file
            pid = str(random.randint(0, 100000))    # set pid
            filename = 'ori.json'                   # get a random file name
            upload_folder = app.config['UPLOAD_FOLDER'] + "/" + pid   # set upload FOLDER
            os.mkdir(upload_folder)   # mkdir
            file.save(os.path.join(upload_folder, filename))          # save file
            return redirect(url_for('show_image1', pid=pid))
        else:
            flash("檔案名稱錯誤(非 json 檔案)", 'danger')
            return render_template('upload_json.html')
    else:
        return render_template('upload_json.html')


# page pid mode
@app.route('/pid_mode', methods=['POST', 'GET'])
def pid_mode():
    if 'goto_pid' in request.form.keys():
        return redirect(url_for('show_image1', pid=request.form['pid']))
    else:
        return render_template('pid_mode.html')


# page show image
@app.route('/show_image1/<pid>', methods=['GET', 'POST'])
def show_image1(pid=None):
    if not pid:
        return redirect(url_for('index'))

    # get json folder

    # create Class ToolBox use json mode
    try:
        tb = ToolBox(jsonf="%s/%s.json" % (FOLDER + '/' + str(pid), 'ori'))
    except FileNotFoundError as e:
        return render_template('404.html'), 404
    except json.decoder.JSONDecodeError:
        return render_template("show_image1.html", data=[], pid=pid)

    if request.method != 'POST':
        return render_template('show_image1.html', data=tb.get_data(), pid=pid)

    # split require
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

    # save new .json
    tmp_data = []
    for a, b in form.items():
        tmp_data.append(tb[a].copy())
        tmp_data[-1]['img_link'] = []
        for i in b:
            tmp_data[-1]['img_link'].append(tb[a]['img_link'][i])
    tb = ToolBox(copy_data=tmp_data)
    tb.save_json('%s/%s/%s.json' % (FOLDER, pid, pid))

    # download image button
    if 'download_image' in request.form.keys():
        return redirect(url_for('download', pid=pid))

    # download json button
    elif 'download_json' in request.form.keys():
        return send_from_directory(FOLDER + '/' + pid, pid + '.json', as_attachment=True)


# download progress page
@app.route('/download/<pid>', methods=['GET', 'POST'])
def download(pid=None):
    if not pid:
        return redirect(url_for('index'))
    if request.method != 'POST':
        return render_template('download.html', pid=pid)
    # download image
    if 'start_download' in request.form.keys():
        return send_from_directory(FOLDER + '/' + pid, pid + '.tar.gz', as_attachment=True)
    # download json
    elif 'json_download' in request.form.keys():
        return send_from_directory(FOLDER + '/' + pid, pid + '.json', as_attachment=True)
    # previous page
    elif 'prev_page' in request.form.keys():
        return redirect(url_for('show_image1', pid=pid))


# progress bar port
@app.route('/progress/<pid>', methods=['GET', 'POST'])
def progress(pid):
    # get path
    # create Class ToolBox
    tb = ToolBox(jsonf="%s/%s/%s.json" % (FOLDER, pid, pid))

    def downloading():
        # source FOLDER
        source_dir = '%s/%s/pictures%s' % (FOLDER, pid, pid)
        # target file
        output = '%s/%s/%s.tar.gz' % (FOLDER, pid, pid)
        # total length of select data
        num = len(tb)
        i = 0

        # download image to server
        for i, j in tb.download_image(source_dir):
            # get percentage
            percent = int(i / (num + 2) * 100)
            yield 'data:' + str('%d' % (percent)) + '\n\n'
        yield 'data:' + str(int((i + 1) / (num + 2) * 100)) + '\n\n'

        # zip the file
        with tarfile.open(output, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
        time.sleep(2)
        yield 'data:100\n\n'

    # connect to progress bar
    return Response(downloading(), mimetype='text/event-stream')


# page about me
@app.route('/aboutme', methods=['GET'])
def aboutme():
    return render_template('aboutme.html')


# page 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    # http_server = WSGIServer(('', 5000), app)
    # http_server.serve_forever()
    # monkey.patch_all()
    # gunicorn -b 127.0.0.1:5000 -w 2 main:app --timeout 2000
    app.run(debug=True)
