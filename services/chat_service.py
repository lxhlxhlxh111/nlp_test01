import os
from typing import List, Dict, AsyncGenerator, Any, Union
import asyncio

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
organization_id = os.getenv('OPENAI_ORGANIZATION_ID')

client = OpenAI(organization=organization_id)

# Create an instance of the FastAPI class
app = FastAPI()

# Define a route for the root URL
@app.get("/")
def read_root():
    return {"Hello": "World"}

instruction_chat = "你的任务是扮演一个擅长聊天的人，会主动发起有趣的话题。"

def create_system_message(instruction):
    system_message = {
        "role": "system",
        "content": f"{instruction}"
    }

    return system_message

class ChatInput(BaseModel):
    messages: List[Dict[str, str]] = []
    temperature: float = 0.5

async def chat_stream(ChatInput) -> AsyncGenerator[Any, Any]:
    stream = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=ChatInput.messages,
        temperature=ChatInput.temperature,
        stream=True
    )

    # Streaming the tokens
    for chunk in stream:
        # print(chunk.choices[0].delta.content or "", end="")
        text_delta = chunk.choices[0].delta.content or ""
        print(text_delta, end="")
        yield text_delta

@app.post("/chat/")
async def chat_api(chat_input: ChatInput):
    system_message = create_system_message(instruction_chat)
    chat_input.messages.insert(0, system_message)

    print(chat_input.messages)

    return StreamingResponse(chat_stream(chat_input))

async def generate_data() -> AsyncGenerator[Any, Any]:
    for i in range(10):
        yield f"data {i}\n"
        # yield b"some fake video bytes"
        await asyncio.sleep(1)

# Route to stream data
@app.get("/stream_test/")
async def stream_test():
    return StreamingResponse(generate_data())