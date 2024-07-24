from flask import Flask, request, jsonify,redirect
from hashids import Hashids
import sqlite3

app = Flask(__name__)

# 配置
HASHIDS_SALT = 'this is my salt'
HASHIDS_MIN_LENGTH = 6

# 短链域名
SHORT_URL_DOMAIN = 'http://localhost:5000/'

# 初始化Hashids
hashids = Hashids(salt=HASHIDS_SALT, min_length=HASHIDS_MIN_LENGTH)

# 初始化SQLite
conn = sqlite3.connect('urls.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS urls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        short_code TEXT UNIQUE,
        long_url TEXT UNIQUE
    )
''')
conn.commit()

@app.route('/shorten', methods=['POST'])
def shorten_url():
    long_url = request.json.get('url')
    if not long_url:
        return jsonify({'error': 'Invalid URL'}), 400

    # 查询数据库看是否已经存在
    c.execute('SELECT short_code FROM urls WHERE long_url = ?', (long_url,))
    result = c.fetchone()
    if result:
        short_code = result[0]
        short_url = SHORT_URL_DOMAIN + short_code
        return jsonify({'short_url': short_url})

    # 插入新的长链接，并获取自增ID
    c.execute('INSERT INTO urls (long_url) VALUES (?)', (long_url,))
    conn.commit()
    url_id = c.lastrowid

    # 生成短码字符串
    short_code = hashids.encode(url_id)

    # 更新数据库中的短码
    c.execute('UPDATE urls SET short_code = ? WHERE id = ?', (short_code, url_id))
    conn.commit()

    # 拼接短链接
    short_url = SHORT_URL_DOMAIN + short_code

    return jsonify({'short_url': short_url})

@app.route('/<short_code>', methods=['GET'])
def redirect_to_long_url(short_code):
    # 从SQLite中查询长链接
    c.execute('SELECT long_url FROM urls WHERE short_code = ?', (short_code,))
    result = c.fetchone()
    if result:
        long_url = result[0]
        return redirect(long_url)
    else:
        return jsonify({'error': 'URL not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)