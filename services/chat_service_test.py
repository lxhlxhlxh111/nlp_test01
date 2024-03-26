import requests

url = "http://127.0.0.1:8000/chat/"

messages = [
    {"role": "user",
     "content": "Hello!"},
    {"role": "assistant",
     "content": "Hi, how can I help you?"},
    {"role": "user", 
     "content": "Compose a poem that explains the concept of recursion in programming."}
]

chat_input = {
    "messages": messages
}

s = requests.Session()

with s.post(url, json=chat_input , stream=True) as resp:
    # delta or chunk
    for delta in resp.iter_content(chunk_size=None):
        delta = delta.decode("utf-8")
        print(delta, end="", flush=True)

    # for chunk in resp.raw.stream():
    #     # print(f"chunk size: {len(chunk)}")
    #     print(chunk, end="")
    # for line in resp.iter_lines():
    #     print(line)
    #     if line:
    #         pass

