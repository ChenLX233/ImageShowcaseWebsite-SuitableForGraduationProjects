import os
import sqlite3
import uuid
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, session, make_response
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ADMIN_PASSWORD = '114514'  # 请改为自己的管理员密码

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = '传奇2h2g宕机王-io读写红漫天'  # 请改为自己的随机字符串
app.config['MAX_CONTENT_LENGTH'] = 12 * 1024 * 1024  # 12MB图片大小限制

# ------------------ 数据库初始化 ------------------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_ip TEXT,
            device_id TEXT,
            username TEXT,
            PRIMARY KEY (user_ip, device_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            uploader_ip TEXT,
            uploader_device TEXT,
            upload_time TEXT,
            likes INTEGER DEFAULT 0,
            uploader_name TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_id INTEGER,
            user_ip TEXT,
            user_device TEXT,
            username TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_id INTEGER,
            user_ip TEXT,
            user_device TEXT,
            username TEXT,
            comment TEXT,
            comment_time TEXT,
            parent_id INTEGER,
            likes INTEGER DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS upload_log (
            device_id TEXT,
            user_ip TEXT,
            upload_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_username():
    user_ip = request.remote_addr
    device_id = request.cookies.get('device_id')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT username FROM users WHERE user_ip=? AND device_id=?', (user_ip, device_id))
    row = c.fetchone()
    conn.close()
    return row[0] if row and row[0] else None

# ------------------ 用户名设置 ------------------
@app.route('/set_username', methods=['POST'])
def set_username():
    username = request.form['username']
    user_ip = request.remote_addr
    device_id = request.cookies.get('device_id')
    if not device_id:
        device_id = str(uuid.uuid4())
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('REPLACE INTO users (user_ip, device_id, username) VALUES (?, ?, ?)', (user_ip, device_id, username))
    conn.commit()
    conn.close()
    resp = redirect(request.referrer or url_for('index'))
    resp.set_cookie('device_id', device_id, max_age=10*365*24*60*60)
    return resp

# ------------------ 管理员登录/登出 ------------------
@app.route('/admin_login', methods=['POST'])
def admin_login():
    password = request.form['admin_password']
    if password == ADMIN_PASSWORD:
        session['is_admin'] = True
    return redirect(request.referrer or url_for('index'))

@app.route('/admin_logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

# ------------------ 首页 ------------------
@app.route('/')
def index():
    if 'device_id' not in request.cookies:
        device_id = str(uuid.uuid4())
        resp = make_response(redirect(url_for('index')))
        resp.set_cookie('device_id', device_id, max_age=10*365*24*60*60)
        return resp
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM images ORDER BY upload_time DESC')
    images = c.fetchall()
    conn.close()
    username = get_username()
    return render_template('index.html', images=images, username=username, is_admin=session.get('is_admin', False))

# ------------------ 上传频率限制 ------------------
def too_many_uploads(device_id, user_ip):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    two_min_ago = (datetime.now() - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M:%S')
    c.execute('SELECT COUNT(*) FROM upload_log WHERE device_id=? AND user_ip=? AND upload_time>=?', (device_id, user_ip, two_min_ago))
    count = c.fetchone()[0]
    conn.close()
    return count >= 1  # 2分钟内超过1次则禁止

# ------------------ 上传图片 ------------------
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        device_id = request.cookies.get('device_id')
        user_ip = request.remote_addr
        is_admin = session.get('is_admin', False)

        # 上传频率限制，管理员不受限
        if not is_admin and too_many_uploads(device_id, user_ip):
             return render_template('upload_limit.html', username=get_username()), 429

        file = request.files.get('file')
        if file and allowed_file(file.filename):
            # 再次后端检查文件大小（防止绕过MAX_CONTENT_LENGTH）
            file.seek(0, os.SEEK_END)
            filesize = file.tell()
            file.seek(0)
            if filesize > 12 * 1024 * 1024:
                return "图片大小不能超过12MB！", 413

            filename = datetime.now().strftime('%Y%m%d%H%M%S_') + secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            username = get_username()
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute('INSERT INTO images (filename, uploader_ip, uploader_device, upload_time, uploader_name) VALUES (?, ?, ?, ?, ?)',
                      (filename, user_ip, device_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), username))
            # 记录上传行为
            c.execute('INSERT INTO upload_log (device_id, user_ip, upload_time) VALUES (?, ?, ?)', (device_id, user_ip, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    username = get_username()
    return render_template('upload.html', username=username)

# ------------------ 图片详情 ------------------
@app.route('/image/<int:image_id>')
def image_detail(image_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM images WHERE id=?', (image_id,))
    image = c.fetchone()
    c.execute('SELECT * FROM comments WHERE image_id=? ORDER BY comment_time ASC', (image_id,))
    comments = c.fetchall()
    conn.close()
    username = get_username()
    is_admin = session.get('is_admin', False)
    return render_template('image.html', image=image, comments=comments, username=username, is_admin=is_admin)

# ------------------ 下载图片 ------------------
@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# ------------------ 删除图片 ------------------
@app.route('/delete/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT filename, uploader_ip, uploader_device FROM images WHERE id=?', (image_id,))
    img = c.fetchone()
    if not img:
        conn.close()
        return jsonify({'success': False, 'message': '图片不存在'})
    user_ip = request.remote_addr
    user_device = request.cookies.get('device_id')
    is_admin = session.get('is_admin', False)
    if (img[1] == user_ip and img[2] == user_device) or is_admin:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img[0]))
        except Exception:
            pass
        c.execute('DELETE FROM images WHERE id=?', (image_id,))
        c.execute('DELETE FROM likes WHERE image_id=?', (image_id,))
        c.execute('DELETE FROM comments WHERE image_id=?', (image_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    else:
        conn.close()
        return jsonify({'success': False, 'message': '无权限删除'})

# ------------------ 点赞 ------------------
@app.route('/like/<int:image_id>', methods=['POST'])
def like(image_id):
    user_ip = request.remote_addr
    device_id = request.cookies.get('device_id')
    username = get_username()
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM likes WHERE image_id=? AND user_ip=? AND user_device=?', (image_id, user_ip, device_id))
    if c.fetchone() is None:
        c.execute('INSERT INTO likes (image_id, user_ip, user_device, username) VALUES (?, ?, ?, ?)', (image_id, user_ip, device_id, username))
        c.execute('UPDATE images SET likes = likes + 1 WHERE id=?', (image_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    conn.close()
    return jsonify({'success': False, 'message': '您已经点过赞了'})

# ------------------ 点赞用户名单 ------------------
@app.route('/like_users/<int:image_id>')
def like_users(image_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT username FROM likes WHERE image_id=?', (image_id,))
    users = [row[0] or '匿名' for row in c.fetchall()]
    conn.close()
    return jsonify(users)

# ------------------ 评论 ------------------
@app.route('/comment/<int:image_id>', methods=['POST'])
def comment(image_id):
    user_ip = request.remote_addr
    device_id = request.cookies.get('device_id')
    username = get_username()
    comment_text = request.form['comment']
    parent_id = request.form.get('parent_id')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO comments (image_id, user_ip, user_device, username, comment, comment_time, parent_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
              (image_id, user_ip, device_id, username, comment_text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), parent_id))
    conn.commit()
    conn.close()
    return redirect(url_for('image_detail', image_id=image_id))

# ------------------ 评论点赞 ------------------
@app.route('/comment_like/<int:comment_id>', methods=['POST'])
def comment_like(comment_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('UPDATE comments SET likes = likes + 1 WHERE id=?', (comment_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ------------------ 删除评论（本人和管理员） ------------------
@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    user_ip = request.remote_addr
    user_device = request.cookies.get('device_id')
    is_admin = session.get('is_admin', False)
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT user_ip, user_device FROM comments WHERE id=?', (comment_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'message': '评论不存在'})
    # 权限: 本人或管理员
    if (row[0] == user_ip and row[1] == user_device) or is_admin:
        # 删除该评论及其所有子评论
        def delete_with_replies(cid):
            c.execute('SELECT id FROM comments WHERE parent_id=?', (cid,))
            sub_ids = [r[0] for r in c.fetchall()]
            for sub_id in sub_ids:
                delete_with_replies(sub_id)
            c.execute('DELETE FROM comments WHERE id=?', (cid,))
        delete_with_replies(comment_id)
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    else:
        conn.close()
        return jsonify({'success': False, 'message': '无权限删除'})

# ------------------ 启动 ------------------
if __name__ == '__main__':
    if not os.path.exists('database.db'):
        init_db()
    else:
        # 补充表结构，确保 uploader_name 字段存在
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("PRAGMA table_info(images)")
        columns = [col[1] for col in c.fetchall()]
        if 'uploader_name' not in columns:
            try:
                c.execute("ALTER TABLE images ADD COLUMN uploader_name TEXT")
                conn.commit()
            except Exception:
                pass
        # 补充表结构，确保 upload_log 表存在
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='upload_log'")
        if not c.fetchone():
            c.execute('''
                CREATE TABLE IF NOT EXISTS upload_log (
                    device_id TEXT,
                    user_ip TEXT,
                    upload_time TEXT
                )
            ''')
            conn.commit()
        conn.close()
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(host='0.0.0.0', port=8000, debug=True)
