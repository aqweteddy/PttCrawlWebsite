from flask import Flask, flash, render_template, request, redirect, url_for,  send_from_directory
from flask_bootstrap import Bootstrap
from crawler.crawler import ToolBox, ThreadList
import random
import tarfile
import os


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


def downloading(tb, pid):
    cur = os.path.dirname(os.path.abspath(__file__))
    source_dir = '%s/pictures%s' % (cur, pid)
    output = '%s/%s.tar.gz' % (cur, pid)
    tb.download_image(source_dir)
    os.chdir(cur)

    print(output, source_dir)

    with tarfile.open(output, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))
    return source_dir, output


@app.route('/', methods=['GET', 'POST'])
def index():
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
            return redirect(url_for('show_image1', pid=pid))

    return render_template('page_mode.html', pid=pid)
    # return render_template('page_mode.html')


@app.route('/show_image1/<pid>', methods=['GET', 'POST'])
def show_image1(pid):
    cur = os.path.dirname(os.path.abspath(__file__))
    print(cur)
    tb = ToolBox(jsonf='%s/crawler/%s.json' % (cur, pid))

    if request.method != 'POST':
        return render_template('show_image1.html', data=tb.data.get_img_link(), pid=pid)

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
    tb.save_json('%s.json' % (pid))

    if 'download_image' in request.form.keys():
        downloading(tb, pid)
        return send_from_directory(app.root_path, pid + '.tar.gz', as_attachment=True)

    elif 'download_json' in request.form.keys():
        return send_from_directory(app.root_path, pid + '.json', as_attachment=True)


@app.route('/download/<pid>', methods=['GET', 'POST'])
def download(pid):
    if request.method == 'GET':
        return send_from_directory(app.root_path, pid + '.tar.gz', as_attachment=True)
    else:
        return redirect(url_for('show_image1', pid=pid))

if __name__ == '__main__':
    # http_server = WSGIServer(('', 5000), app)
    # http_server.serve_forever()
    # monkey.patch_all()
    # gunicorn -b 127.0.0.1:5000 -w 2 main:app --timeout 2000
    app.run(debug=True)
