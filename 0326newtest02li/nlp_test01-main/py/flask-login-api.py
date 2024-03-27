from flask import Flask, render_template, request, g, request, jsonify, redirect, url_for, session


import openai
import sqlite3
import traceback
app = Flask(__name__, static_url_path='/static')

DATABASE = 'users.db'
with open('./key.txt', 'r') as file:
    api_key = file.read().strip()
openai.api_key = api_key
# print("api_key",api_key)
# 用于保存对话历史的全局变量
conversation_history = []
system_message_added = False  # Flag to check if system message has been added
#session密钥
app.secret_key = 'Cxh12300'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/regist')
def regist():
    return render_template('regist.html')

@app.route('/registuser', methods=['POST'])
def getRigistRequest():
    try:
        if request.method == 'POST':
            username = request.form.get('user')
            password = request.form.get('password')

            conn = get_db()
            cursor = conn.cursor()
            
            sql = "INSERT INTO user(user, password) VALUES (?, ?)"
            cursor.execute(sql, (username, password))
            
            conn.commit()
            
            return  redirect(url_for('login'))
        else:
            # return '不支持的请求方法'
            return render_template('login.html')
    except Exception as e:
        traceback.print_exc()
        return '注册失败'

@app.route('/login', methods=['POST'])
def getLoginRequest():
    try:
        username = request.form.get('user')
        password = request.form.get('password')

        conn = get_db()
        cursor = conn.cursor()
        
        sql = "SELECT * FROM user WHERE user=? AND password=?"
        cursor.execute(sql, (username, password))
        user = cursor.fetchone()
        print("user",user)
        if user:
            # 将用户信息保存到 session 中
            name = user[0]
            user_id = user[2]
            # print(name)
            # print(user_id)
            return render_template('index.html',name=name, user_id=user_id)
        else:
            return '用户名或密码不正确'
    except Exception as e:
        traceback.print_exc()
        return '登录失败'


@app.route('/chat', methods=['POST'])
def chat():
    global conversation_history
    global system_message_added

    data = request.get_json()

    user_message = data['message']

    # 如果系统消息尚未添加，则添加到对话历史中
    if not system_message_added:
        system_message = ("The opening statement you must say: I am your digital person and you can chat with me"
                          "##You are an all-knowing and empathetic prophet. "
                          "##You like to ask proactive question after every answer. "
                          "##You like to ask others about their hobbies, age, gender, and you like to make friends. "
                          "The questions cannot be exactly the same every time."
                          "You must choose a different topic each time"
                          "##You are friendly.")
        conversation_history.append({"role": "system", "content": system_message})
        system_message_added = True

    # 添加用户消息到对话历史
    conversation_history.append({"role": "user", "content": user_message})
    # print(conversation_history)

    # 向OpenAI发送对话历史并获取回复
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
        messages=conversation_history,
        temperature=0.1
    )

    # 获取AI回复并将其添加到对话历史
    reply = response["choices"][0]["message"]["content"]
    conversation_history.append({"role": "system", "content": reply})
    print(conversation_history)
    # print(jsonify({"reply": reply}))

    return jsonify({"reply": reply})
    # return conversation_history

if __name__ == '__main__':
    app.run(debug=True,port=5003)
