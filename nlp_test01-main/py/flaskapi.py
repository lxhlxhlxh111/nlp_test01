from flask import Flask, request, jsonify
import openai
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources=r'*')

conn = sqlite3.connect('chat1.db')
cursor = conn.cursor()

with open('../key.txt', 'r') as file:
    api_key = file.read().strip()
openai.api_key = api_key

# 用于保存对话历史的全局变量
conversation_history = []
system_message_added = False  # Flag to check if system message has been added


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

if __name__ == "__main__":
    app.run(port=5003, debug=True)
