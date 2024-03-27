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
instruction_chat = "你的任务是扮演一个擅长聊天的人，会主动发起有趣的话题。"

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



def respond_stream(new_content, chat_history, temperature=0.8):

    messages = collect_messages(new_content, chat_history, instruction_chat)
    chat_history = chat_history + [[new_content, ""]]
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
        acc_text += text_delta
        last_turn = list(chat_history.pop(-1))
        last_turn[-1] += acc_text
        chat_history = chat_history + [last_turn]
        yield "", chat_history
        acc_text = ""


with gr.Blocks() as demo:
    chatbot = gr.Chatbot(label=instruction_chat, height=240)
    txt_msg1 = gr.Textbox(label="Prompt1")
    txt_msg2 = gr.Textbox(label="Prompt2")
    with gr.Accordion(label="Advanced options", open=False):
        slider_temperature = gr.Slider(label="temperature", minimum=0.1, maximum=1, value=0.8, step=0.1)
    btn_send1 = gr.Button("Send1")
    btn_send1.click(respond_stream, inputs=[txt_msg1, chatbot, slider_temperature], outputs=[txt_msg1, chatbot])
    txt_msg1.submit(respond_stream, inputs=[txt_msg1, chatbot, slider_temperature], outputs=[txt_msg1, chatbot]) #Press enter to submit
  
    btn_send2 = gr.Button("Send2")
    btn_send2.click(respond_stream, inputs=[txt_msg2, chatbot, slider_temperature], outputs=[txt_msg2, chatbot])
    txt_msg2.submit(respond_stream, inputs=[txt_msg2, chatbot, slider_temperature], outputs=[txt_msg2, chatbot]) #Press enter to submit
  
if __name__ == "__main__":
    gr.close_all()

   
    demo.queue().launch(share=True)
    gr.close_all()

