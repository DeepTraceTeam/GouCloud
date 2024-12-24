from flask import Flask, request, jsonify, send_from_directory, session, render_template_string
import os
import uuid
import random
import string
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

"""
MySQL数据库表创建指令:

CREATE TABLE cloud_user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE cloud_file (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_uuid VARCHAR(36) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES cloud_user(id)
);

CREATE TABLE file_shares (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_uuid VARCHAR(36) NOT NULL,
    share_code VARCHAR(6) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_file_uuid (file_uuid)
);
"""

app = Flask(__name__)
app.secret_key = 'super_secret_key'

UPLOAD_FOLDER = './cloud_file'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 静态文件夹路径
STATIC_FOLDER = './public'

# HTML模板用于显示密码输入框
PASSWORD_PROMPT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>文件分享 - 328云盘</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        .container {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
            width: 90%;
            max-width: 400px;
            text-align: center;
        }
        .logo {
            font-size: 1.5rem;
            color: #333;
            margin-bottom: 1.5rem;
        }
        h2 {
            color: #2c3e50;
            margin-bottom: 1.5rem;
        }
        .error {
            color: #e74c3c;
            background: #fde8e7;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            font-size: 1.1rem;
        }
        .expired {
            font-size: 1.5rem;
            color: #7f8c8d;
            margin: 2rem 0;
        }
        input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s;
            box-sizing: border-box;
        }
        input:focus {
            border-color: #3498db;
            outline: none;
        }
        button {
            background: #3498db;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: background 0.3s;
            width: 100%;
            margin-top: 10px;
        }
        button:hover {
            background: #2980b9;
        }
        .back-home {
            margin-top: 1rem;
            color: #7f8c8d;
            text-decoration: none;
            font-size: 0.9rem;
        }
        .back-home:hover {
            color: #34495e;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">328云盘</div>
        {% if expired %}
            <div class="expired">
                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="15" y1="9" x2="9" y2="15"></line>
                    <line x1="9" y1="9" x2="15" y2="15"></line>
                </svg>
                <p>分享链接已失效</p>
            </div>
        {% else %}
            <h2>访问共享文件</h2>
            {% if error %}
            <p class="error">{{ error }}</p>
            {% endif %}
            <form method="POST">
                <input type="password" name="share_code" placeholder="请输入6位分享密码" maxlength="6" autocomplete="off">
                <button type="submit">下载文件</button>
            </form>
        {% endif %}
        <a href="/" class="back-home">返回首页</a>
    </div>
</body>
</html>
'''

@app.route('/')
def serve_index():
    return send_from_directory(STATIC_FOLDER, 'index.html')

@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory(STATIC_FOLDER, filename)

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'cloud_disk'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',        # 数据库主机
            port=3306,              # MySQL 端口
            user='root',            # 数据库用户名
            password='1024',        # 数据库密码
            database='cloud_disk'   # 数据库名称
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection failed: {err}")
        raise

@app.route('/share/<file_uuid>', methods=['GET', 'POST'])
def access_shared_file(file_uuid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 首先检查文件是否存在且已分享
    cursor.execute("""
        SELECT f.file_name, s.share_code 
        FROM cloud_file f
        LEFT JOIN file_shares s ON f.file_uuid = s.file_uuid
        WHERE f.file_uuid = %s
    """, (file_uuid,))
    
    file = cursor.fetchone()
    
    # 如果文件不存在或没有分享记录
    if not file or not file.get('share_code'):
        cursor.close()
        conn.close()
        return render_template_string(PASSWORD_PROMPT_TEMPLATE, expired=True)
    
    if request.method == 'GET':
        return render_template_string(PASSWORD_PROMPT_TEMPLATE, expired=False)
    
    share_code = request.form.get('share_code')
    if not share_code:
        return render_template_string(PASSWORD_PROMPT_TEMPLATE, error='请输入分享密码', expired=False)
    
    # 验证分享码
    if share_code != file['share_code']:
        return render_template_string(PASSWORD_PROMPT_TEMPLATE, error='分享密码错误', expired=False)
    
    cursor.close()
    conn.close()

    # 密码正确，重定向到下载
    return send_from_directory(
        UPLOAD_FOLDER, 
        file_uuid,
        as_attachment=True,
        download_name=file['file_name']
    )

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 对密码进行加密
        hashed_password = generate_password_hash(password)

        # 插入用户
        cursor.execute("INSERT INTO cloud_user (username, password) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()

        return jsonify({'message': 'User registered successfully'}), 201
    except mysql.connector.Error as err:
        if err.errno == 1062:  # Duplicate entry error
            return jsonify({'error': 'Username already exists'}), 409
        return jsonify({'error': 'Database error: ' + str(err)}), 500
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred: ' + str(e)}), 500
    finally:
        # 确保资源被释放
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cloud_user WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        return jsonify({'success': True, 'user_id': user['id']})
    return jsonify({'success': False, 'message': '用户名或密码错误'})

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return '', 204

@app.route('/files', methods=['GET'])
def list_files():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT f.*, CASE WHEN s.share_code IS NOT NULL THEN TRUE ELSE FALSE END as is_shared 
        FROM cloud_file f 
        LEFT JOIN file_shares s ON f.file_uuid = s.file_uuid 
        WHERE f.user_id = %s
    """, (user_id,))
    files = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(files)

@app.route('/upload', methods=['POST'])
def upload():
    user_id = session.get('user_id')
    if not user_id:
        return 'Unauthorized', 401

    file = request.files['file']
    file_uuid = str(uuid.uuid4())
    file.save(os.path.join(UPLOAD_FOLDER, file_uuid))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO cloud_file (user_id, file_name, file_uuid) VALUES (%s, %s, %s)",
                   (user_id, file.filename, file_uuid))
    conn.commit()
    cursor.close()
    conn.close()

    return '', 204

@app.route('/download/<file_uuid>', methods=['GET'])
def download(file_uuid):
    user_id = session.get('user_id')
    share_code = request.args.get('share_code')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if share_code:
        # 验证分享码
        cursor.execute("""
            SELECT f.file_name 
            FROM cloud_file f
            JOIN file_shares s ON f.file_uuid = s.file_uuid
            WHERE f.file_uuid = %s AND s.share_code = %s
        """, (file_uuid, share_code))
    else:
        # 验证文件所有者
        if not user_id:
            cursor.close()
            conn.close()
            return 'Unauthorized', 401
        cursor.execute("SELECT file_name FROM cloud_file WHERE file_uuid = %s AND user_id = %s", (file_uuid, user_id))
    
    file = cursor.fetchone()
    cursor.close()
    conn.close()

    if not file:
        return 'File not found', 404

    file_name = file['file_name']
    return send_from_directory(UPLOAD_FOLDER, file_uuid, as_attachment=True, download_name=file_name)

@app.route('/api/share/<file_uuid>', methods=['POST'])
def share_file(file_uuid):
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 验证文件所有权
        cursor.execute("SELECT * FROM cloud_file WHERE file_uuid = %s AND user_id = %s", (file_uuid, user_id))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'File not found'}), 404

        # 生成6位随机分享码
        share_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # 创建分享记录
        cursor.execute("""
            INSERT INTO file_shares (file_uuid, share_code) 
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE share_code = VALUES(share_code)
        """, (file_uuid, share_code))
        conn.commit()
        
        # 确保返回的是相对路径
        share_url = f"/share/{file_uuid}"
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'share_code': share_code,
            'share_url': share_url
        })

    except Exception as e:
        print("Error in share_file:", str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/share/<file_uuid>', methods=['DELETE'])
def unshare_file(file_uuid):
    user_id = session.get('user_id')
    if not user_id:
        return 'Unauthorized', 401

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 验证文件所有权
    cursor.execute("SELECT * FROM cloud_file WHERE file_uuid = %s AND user_id = %s", (file_uuid, user_id))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return 'File not found', 404

    # 删除分享记录
    cursor.execute("DELETE FROM file_shares WHERE file_uuid = %s", (file_uuid,))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    return '', 204

@app.route('/delete/<file_uuid>', methods=['DELETE'])
def delete_file(file_uuid):
    user_id = session.get('user_id')
    if not user_id:
        return 'Unauthorized', 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cloud_file WHERE file_uuid = %s AND user_id = %s", (file_uuid, user_id))
    file = cursor.fetchone()
    if file:
        os.remove(os.path.join(UPLOAD_FOLDER, file_uuid))
        cursor.execute("DELETE FROM cloud_file WHERE file_uuid = %s", (file_uuid,))
        cursor.execute("DELETE FROM file_shares WHERE file_uuid = %s", (file_uuid,))
        conn.commit()
    cursor.close()
    conn.close()

    return '', 204

@app.route('/api/share/<file_uuid>', methods=['GET'])
def get_share_info(file_uuid):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT s.share_code, f.file_uuid
        FROM cloud_file f
        JOIN file_shares s ON f.file_uuid = s.file_uuid
        WHERE f.file_uuid = %s AND f.user_id = %s
    """, (file_uuid, user_id))
    
    share = cursor.fetchone()
    cursor.close()
    conn.close()

    if not share:
        return jsonify({'error': 'Share not found'}), 404

    return jsonify({
        'share_code': share['share_code'],
        'share_url': f"/share/{file_uuid}"
    })

@app.route('/api/destroy-account', methods=['POST'])
def destroy_account():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401

    data = request.get_json()
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 验证密码
        cursor.execute("SELECT password FROM cloud_user WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user or not check_password_hash(user['password'], password):
            return jsonify({'success': False, 'message': '密码错误'}), 401

        # 获取用户文件列表
        cursor.execute("SELECT file_uuid FROM cloud_file WHERE user_id = %s", (user_id,))
        files = cursor.fetchall()

        # 删除物理文件
        for file in files:
            file_path = os.path.join(UPLOAD_FOLDER, file['file_uuid'])
            if os.path.exists(file_path):
                os.remove(file_path)

        # 删除数据库记录（按顺序删除以遵守外键约束）
        cursor.execute("DELETE FROM file_shares WHERE file_uuid IN (SELECT file_uuid FROM cloud_file WHERE user_id = %s)", (user_id,))
        cursor.execute("DELETE FROM cloud_file WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM cloud_user WHERE id = %s", (user_id,))
        
        conn.commit()
        session.clear()  # 清除会话
        
        return jsonify({'success': True})

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, use_debugger=True, use_reloader=True)
