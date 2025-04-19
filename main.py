"""
作者: 江承峻
说明: 此为一个用户信息管理系统，详情请看介绍文档
"""

# 从flask模块导入Flask类，用于创建Web应用
from flask import *
# 从pysmx.SM3模块导入hash_msg函数，用于密码哈希
from pysmx.SM3 import hash_msg
# 从waitress模块导入serve函数，用于运行Web服务器
from waitress import serve
# 导入json模块，用于读写JSON文件
import json
# 导入random模块，用于生成随机字符串
import random
# 导入string模块，用于获取字母和数字字符集
import string
# 导入time模块，用于获取当前时间戳
import time

# 初始化Flask应用
app = Flask(__name__)

# 采用JSON格式读取用户信息
# 如果文件不存在，则初始化空列表
try:
    # 打开users.json文件，读取所有用户信息（用户名和密码哈希）
    with open('users.json', 'r') as f:
        users = json.load(f)  # 存储用户信息的列表
    # 打开usernames.json文件，读取所有用户名
    with open('usernames.json', 'r') as f:
        usernames = json.load(f)  # 存储用户名的列表
    # 打开nicknames.json文件，读取所有用户昵称
    with open('nicknames.json', 'r') as f:
        nicknames = json.load(f)  # 存储用户昵称的列表
except:
    # 如果文件不存在，初始化空列表
    usernames = []
    users = []
    nicknames = []

# 存储用户登录密钥的列表
userkeys = []

# 定义根路由，返回主页
@app.route('/')
def index():
    return render_template('index.html', msg = '')

# 定义登录路由，处理POST请求
@app.route('/login', methods = ['POST'])
def login():
    # 获取POST请求中的密码字段
    password = request.form['password']
    # 获取POST请求中的用户名字段
    username = request.form['username']
    # 对密码进行哈希处理
    hashmsg = hash_msg(password)
    # 如果用户名存在且密码哈希匹配，则登录成功，生成会话密钥
    if username in usernames and {'username': username, 'password': hashmsg} in users:
        # 生成8位随机字符串和时间戳，拼接为会话密钥，有效期为1天
        userkey = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8)) + '/' + str(int(time.time()) + 86400)
        # 获取用户ID
        userid = usernames.index(username)
        # 将用户会话密钥加入列表
        userkeys.append({'userid': int(userid), 'userkey': userkey})
        # 返回登录成功信息和用户ID、会话密钥
        return render_template('index.html', msg = 'login success', userid = userid, userkey = userkey)
    else:
        # 登录失败，返回错误信息
        return render_template('index.html', msg = 'login fail')

# 定义注册路由，处理POST请求
@app.route('/register', methods = ['POST'])
def register():
    # 获取POST请求中的密码字段
    password = request.form['password']
    # 获取POST请求中的用户名字段
    username = request.form['username']
    # 获取POST请求中的昵称字段
    nickname = request.form['nickname']
    # 如果用户名、密码或昵称字段为空，则注册失败
    if nickname == None or password == None or username == None:
        return render_template('index.html', msg ='register fail')
    # 对密码进行哈希处理
    hashmsg = hash_msg(password)
    # 如果用户名不存在，则添加用户信息并保存到文件
    if username not in usernames:
        users.append({'username': username, 'password': hashmsg})
        usernames.append(username)
        nicknames.append(nickname)
        # 将用户信息写入users.json文件
        with open('users.json', 'w') as f:
            json.dump(users, f)
        # 将用户名写入usernames.json文件
        with open('usernames.json', 'w') as f:
            json.dump(usernames, f)
        # 将用户昵称写入nicknames.json文件
        with open('nicknames.json', 'w') as f:
            json.dump(nicknames, f)
        # 返回注册成功信息
        return render_template('index.html', msg = 'register success')
    else:
        # 用户名已存在，返回错误信息
        return render_template('index.html', msg = 'register fail')

# 定义登出路由，处理GET请求
@app.route('/logout', methods = ['GET'])
def logout():
    # 获取GET请求中的用户ID参数
    userid = request.args.get('userid')
    # 获取GET请求中的会话密钥参数
    userkey = request.args.get('userkey')
    # 从用户会话密钥列表中移除该用户的会话密钥
    userkeys.remove({'userid': int(userid), 'userkey': userkey})
    # 返回登出信息
    return render_template('index.html', msg = 'logout')

# 定义修改密码路由，处理POST请求
@app.route('/change_password', methods = ['POST'])
def change_password():
    # 获取POST请求中的用户ID字段
    userid = request.form.get('userid')
    # 获取POST请求中的会话密钥字段
    userkey = request.form.get('userkey')
    # 获取POST请求中的旧密码字段
    old_password = request.form.get('old_password')
    # 获取POST请求中的新密码字段
    new_password = request.form.get('new_password')
    # 获取POST请求中的确认新密码字段
    renew_password = request.form.get('renew_password')
    # 如果用户ID或会话密钥为空，或会话密钥已过期，则登出用户
    if userid == None or userkey == None or userkey.find('/') != userkey.rfind('/') or int(userkeys[userkeys.index({'userid': int(userid), 'userkey': userkey})]['userkey'].split('/')[1]) < int(time.time()):
        return render_template('index.html', msg = 'logout')
    else:
        # 如果旧密码、新密码不为空且新密码与确认密码相同，且旧密码哈希匹配，则修改密码并保存到文件
        if old_password != None and new_password != None and new_password == renew_password and hash_msg(old_password) == users[int(userid)]['password']:
            users[int(userid)]['password'] = hash_msg(new_password)
            # 将用户信息写入users.json文件
            with open('users.json', 'w') as f:
                json.dump(users, f)
            # 从用户会话密钥列表中移除该用户的会话密钥
            userkeys.remove({'userid': int(userid), 'userkey': userkey})
            # 返回修改密码成功信息
            return render_template('services.html', users = users, userid = int(userid), userkey = userkey, nicknames = nicknames, msg = 'change password success')
        # 返回修改密码失败信息
        return render_template('services.html', users = users, userid = int(userid), userkey = userkey, nicknames = nicknames, msg = 'change password fail')

# 定义修改昵称路由，处理POST请求
@app.route('/change_nickname', methods = ['POST'])
def change_nickname():
    # 获取POST请求中的用户ID字段
    userid = request.form.get('userid')
    # 获取POST请求中的会话密钥字段
    userkey = request.form.get('userkey')
    # 获取POST请求中的新昵称字段
    nickname = request.form.get('new_nickname')
    # 如果用户ID或会话密钥为空，或会话密钥已过期，则登出用户
    if userid == None or userkey == None or userkey.find('/') != userkey.rfind('/') or int(userkeys[userkeys.index({'userid': int(userid), 'userkey': userkey})]['userkey'].split('/')[1]) < int(time.time()):
        return render_template('index.html', msg = 'logout')
    else:
        try:
            # 如果新昵称不为空，则修改昵称并保存到文件
            if nickname != None:
                nicknames[int(userid)] = nickname
                # 将用户昵称写入nicknames.json文件
                with open('nicknames.json', 'w') as f:
                    json.dump(nicknames, f)
            else:
                nicknames[int(userid)] = ""
                # 将用户昵称写入nicknames.json文件
                with open('nicknames.json', 'w') as f:
                    json.dump(nicknames, f)
            # 返回修改昵称成功信息
            return render_template('services.html', users = users, userid = int(userid), userkey = userkey, nicknames = nicknames, msg = 'change nickname success')
        except:
            # 返回修改昵称失败信息
            return render_template('services.html', users = users, userid = int(userid), userkey = userkey, nicknames = nicknames, msg = 'change nickname fail')

# 定义服务路由，处理GET请求
@app.route('/services', methods = ['GET'])
def services():
    # 获取GET请求中的用户ID参数
    userid = request.args.get('userid')
    # 获取GET请求中的会话密钥参数
    userkey = request.args.get('userkey')
    # 如果用户ID或会话密钥为空，或会话密钥已过期，则登出用户
    if userid == None or userkey == None or userkey.find('/') != userkey.rfind('/') or int(userkeys[userkeys.index({'userid': int(userid), 'userkey': userkey})]['userkey'].split('/')[1]) < int(time.time()):
        return render_template('index.html', msg = 'logout')
    else:
        # 返回服务页面，显示用户信息和昵称
        return render_template('services.html', users = users, userid = int(userid), userkey = userkey, nicknames = nicknames, msg = '')

if __name__ == '__main__':
    print("访问地址：http://localhost:8080")
    # 启动Web服务器，监听所有IP地址的8080端口
    serve(app, host = '0.0.0.0', port = 8080)