import os
import io
import time
import re
import tempfile
import shutil

import gradio as gr
import sqlite3
from dotenv import load_dotenv
from openai import OpenAI
import json

load_dotenv()
organization_id = os.getenv('OPENAI_ORGANIZATION_ID')

client = OpenAI(organization=organization_id)

# SQLite database initialization
with sqlite3.connect("user_infos.db") as connection:
    cursor = connection.cursor()

    # Create a table to store chat information
    cursor.execute(
        '''\
        CREATE TABLE IF NOT EXISTS user_infos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            username TEXT NOT NULL,
            personality TEXT,
            facts TEXT
        )\
        '''
    )
    connection.commit()

def create_system_message(instruction):
    system_message = {
        "role": "system",
        "content": f"{instruction}"
    }

    return system_message

def collect_messages(new_content, chat_history, instruction):
    messages = []
    system_message = create_system_message(instruction)
    messages.append(system_message)

    for turn in chat_history:
        user_content, assistant_content = turn
        user_message = {
            "role": "user",
            "content": f"{user_content}"
        }

        assistant_message = {
            "role": "assistant",
            "content": f"{assistant_content}"
        }
        messages.append(user_message)
        messages.append(assistant_message)
    latest_user_message = {
        "role": "user",
        "content": f"{new_content}"
    }
    messages.append(latest_user_message)
    return messages

instruction_chat = "你的任务是扮演一个擅长聊天的人，会主动发起有趣的话题。"
instruction_extract_template = """\
分析下面给出的对话，分析user是个什么样的人，然后如果有值得记录的有趣的事实或事情，也记录下来，如果没有，就不记录。给出的对话被三个反引号标识：
```
{dialogue}
```

请按照以下格式输出：
<personality>(这里是user是个什么样的人)</personality>
<facts>(这里是user有趣的事实或事情，如果没有值得记录的事情，就不要输出整个<facts></facts>内容以及<facts>标签)</facts>\
"""

# https://stackoverflow.com/questions/39948645/how-to-use-str-format-inside-a-string-of-json-format
instruction_extract_json_template = """\
分析下面给出的对话，分析user是个什么样的人，然后如果有值得记录的有趣的事实或事情，也记录下来，如果没有，就不记录。给出的对话被三个反引号标识：
```
{dialogue}
```

输出格式为JSON格式，没有其他的东西。JSON包含personality和facts两个键。personality的值为user是什么样的人，facts是有趣的事实。具体输出格式如下：
{{
    "personality": <字符串类型>,
    "facts": <字符串类型，如果没有，就填null>
}}
"""

instruction_drunk_heavily_template = """\
你的任务是扮演一个大醉的人，他酒后吐真言，聊天时会不自主地揭发以下用户的信息：

个性：{personality}
事实：{facts}
"""

instruction_drunk_lightly = """\
你的任务是扮演一个微微醉酒的人，他会吹牛逼
"""

class DrunkLevel:
    LIGHTLY = 0
    HEAVILY = 1

    LIGHTLY_STR = "轻度"
    HEAVILY_STR = "重度"

    str_to_value = {
        LIGHTLY_STR: LIGHTLY,
        HEAVILY_STR: HEAVILY,
    }

# def respond()

def respond_stream(new_content, chat_history, temperature=0.8):
    # Maybe I should use gr.Interface.block()

    messages = collect_messages(new_content, chat_history, instruction_chat)
    chat_history = chat_history + [[new_content, ""]]

    # print(messages)

    stream = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=messages,
        temperature=temperature,
        stream=True
    )

    # accumulated text
    acc_text = ""
    # Streaming the tokens
    for chunk in stream:
        # print(chunk.choices[0].delta.content or "", end="")
        text_delta = chunk.choices[0].delta.content or ""

        # if response.details:
        #     return

        # if idx == 0 and text_token.startswith(" "):
        #     text_token = text_token[1:]

        acc_text += text_delta
        last_turn = list(chat_history.pop(-1))
        last_turn[-1] += acc_text
        chat_history = chat_history + [last_turn]
        yield "", chat_history
        acc_text = ""

def respond_stream_drunk(drunk_level_str, personality, facts, new_content, chat_history, temperature=1.0):
    drunk_level = DrunkLevel.str_to_value[drunk_level_str]

    if drunk_level == DrunkLevel.LIGHTLY:
        instruction_drunk = instruction_drunk_lightly
    elif drunk_level == DrunkLevel.HEAVILY:
        instruction_drunk = instruction_drunk_heavily_template.format(personality=personality, facts=facts)
    else:
        raise gr.Error("请设置合适的醉酒成度！")

    messages = collect_messages(new_content, chat_history, instruction_drunk)
    chat_history = chat_history + [[new_content, ""]]

    # print(messages)

    stream = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=messages,
        temperature=temperature,
        stream=True
    )

    # accumulated text
    acc_text = ""
    # Streaming the tokens
    for chunk in stream:
        # print(chunk.choices[0].delta.content or "", end="")
        text_delta = chunk.choices[0].delta.content or ""

        # if response.details:
        #     return

        # if idx == 0 and text_token.startswith(" "):
        #     text_token = text_token[1:]

        acc_text += text_delta
        last_turn = list(chat_history.pop(-1))
        last_turn[-1] += acc_text
        chat_history = chat_history + [last_turn]
        yield "", chat_history
        acc_text = ""

def save_chat_history(chat_history):
    # temp_bytes = io.BytesIO()
    # for turn in chat_history:
    #     user_content, assistant_content = turn
    #     temp_bytes.write(f"{user_content}\n".encode("utf-8"))
    #     temp_bytes.write(f"{assistant_content}\n".encode("utf-8"))
    # return temp_bytes

    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as temp_file:
            for turn in chat_history:
                user_content, assistant_content = turn
                temp_file.write(f"{user_content}\n")
                temp_file.write(f"{assistant_content}\n")
            temp_file_path = temp_file.name
            print(temp_file_path)
        
        return temp_file_path
    except Exception as e:
        print(f"Error saving file: {e}")
        return None

def upload_chat_history(file):
    print(file)
    chat_history = load_chat_history(file)
    return chat_history

def load_chat_history(file):
    chat_history = []
    with open(file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            turn = (lines[i], lines[i + 1])
            chat_history.append(turn)
        else:
            turn = (lines[i], "")
            chat_history.append(turn)

    return chat_history         

def display_uploaded_file(file):
    print(file)
    return file

def extract_string_between(source, start_str, end_str):
    pattern = re.compile(f'{re.escape(start_str)}(.*?){re.escape(end_str)}')
    match = pattern.search(source)
    
    if match:
        return match.group(1)
    else:
        return ""

def extract_stream_json(chat_history):
    dialogue = ""
    for turn in chat_history:
        #用户输入的关键词和ai给的回答
        user_content, assistant_content = turn
        # print("user_content",user_content)
        # print("assistant_content",assistant_content)
        dialogue +=\
        f"""user: {user_content}
assistant: {assistant_content}
"""
        
    print(dialogue)
    dialogue = dialogue.strip()
    instruction = instruction_extract_json_template.format(dialogue=dialogue)
    instruction = instruction.strip()
    print(instruction)
    
    messages = []
    sys_msg = create_system_message(instruction)
    messages.append(sys_msg)

    print(messages)

    stream = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=messages,
        temperature=0,
        stream=True
    )

    # accumulated text
    acc_text = ""
    # Streaming the tokens
    for chunk in stream:
        # print(chunk.choices[0].delta.content or "", end="")
        text_delta = chunk.choices[0].delta.content or ""
        # print("text_delta",text_delta)
        acc_text += text_delta
        yield acc_text, "{}", "", ""

    print(acc_text)
    try:
        json_object = json.loads(acc_text)
    except ValueError as e:
        print(e)
        yield acc_text, "{}", "", ""
        raise gr.Error("Not a valid JSON string!")

    personality = json_object['personality']
    facts = json_object['facts']

    yield acc_text, json_object, personality, facts

def save_to_database(username, personality, facts):
    # print('111111');
    # print('username',username)
    # print('personality',personality)
    # print('facts',facts)
    with sqlite3.connect("user_infos.db") as connection:
        cursor = connection.cursor()

        # Check if the username already exists
        cursor.execute("SELECT COUNT(*) FROM user_infos WHERE username = ?", (username,))
        count = cursor.fetchone()[0]

        if count != 0:
            try:
                cursor.execute('''\
                    UPDATE user_infos
                    SET personality = ?, facts = ?, timestamp = CURRENT_TIMESTAMP
                    WHERE username = ?\
                    ''',
                    (personality, facts, username)
                )
                connection.commit()
                return "User info updated in SQLite database successfully!"
            except Exception as e:
                return f"Error updating user info in SQLite database: {e}"
        else:
            try:
                cursor.execute('INSERT INTO user_infos (username, personality, facts) VALUES (?, ?, ?)', (username, personality, facts))
                connection.commit()
                return "user_info saved to SQLite database successfully!"
            except Exception as e:
                return f"Error saving to SQLite database: {e}"

with gr.Blocks() as demo:
    # for i in range(2):
    #     _ = gr.Markdown(f"""--{i}--""")

    txt_username = gr.Textbox(label="Your Name")
    chatbot = gr.Chatbot(label=instruction_chat, height=240)
    txt_msg = gr.Textbox(label="Prompt")
    with gr.Accordion(label="Advanced options", open=False):
        slider_temperature = gr.Slider(label="temperature", minimum=0.1, maximum=1, value=0.8, step=0.1)

    btn_upload_chat_history = gr.UploadButton(label="Upload Chat History", file_types=["text"])
    
    btn_send = gr.Button("Send")
    btn_clear = gr.ClearButton(components=[txt_msg, chatbot], value="Clear console")
    btn_save_chat_history = gr.Button("Save Chat History")
    file_chat_history = gr.File(label="Chat History")
 
    btn_extract_json = gr.Button("Extract Information")
    txt_info_structured_output = gr.Textbox(label="Information Structured Output", lines=2)
    json_info = gr.JSON(label="Information in JSON format")

    txt_personality = gr.Textbox(label="特点", lines=2)
    txt_facts = gr.Textbox(label="事实", lines=2)

    btn_save_to_db = gr.Button("Save to Database")

    with gr.Accordion(label="Advanced options",open=True):
        radio_drunk_level = gr.Radio([DrunkLevel.LIGHTLY_STR, DrunkLevel.HEAVILY_STR], label="醉酒成度", value=DrunkLevel.LIGHTLY_STR)

    chatbot_drunk = gr.Chatbot(label="喝醉状态", height=240)
    txt_msg_drunk = gr.Textbox(label="Prompt")
    btn_send_drunk = gr.Button("Send")

    btn_send.click(respond_stream, inputs=[txt_msg, chatbot, slider_temperature], outputs=[txt_msg, chatbot])
    txt_msg.submit(respond_stream, inputs=[txt_msg, chatbot, slider_temperature], outputs=[txt_msg, chatbot]) #Press enter to submit
    
    btn_save_chat_history.click(save_chat_history, inputs=chatbot, outputs=file_chat_history)
    btn_upload_chat_history.upload(upload_chat_history, inputs=btn_upload_chat_history, outputs=chatbot)

    btn_extract_json.click(extract_stream_json, inputs=[chatbot], outputs=[txt_info_structured_output, json_info, txt_personality, txt_facts])

    btn_save_to_db.click(save_to_database, inputs=[txt_username, txt_personality, txt_facts])

    btn_send_drunk.click(respond_stream_drunk,
                        inputs=[radio_drunk_level, txt_personality, txt_facts, txt_msg_drunk, chatbot_drunk],
                        outputs=[txt_msg_drunk, chatbot_drunk])

if __name__ == "__main__":
    gr.close_all()

    cwd = os.getcwd()
    print(cwd)
    temp_dir = tempfile.mkdtemp(dir=cwd)
    tempfile.tempdir = temp_dir
    print(tempfile.tempdir)

    demo.queue().launch(share=True)
    # demo.launch()
    gr.close_all()

    # Delete the temporary directory
    shutil.rmtree(temp_dir)
    
    print("End")
