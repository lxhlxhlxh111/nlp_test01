import time
import openai

def generate_responses(questions):
    for question in questions:
        # 将问题字符串封装为一个对象
        question_obj = {"role": "user", "content": question}
        
        # 调用 OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-1106",
            messages=[question_obj],  # 将问题对象放入数组中
            temperature=0.1
        )
        
        # 遍历并处理每个 Completion 对象
        for completion in response.choices:
            yield completion.message  # 不再使用 strip() 方法
        time.sleep(1)  # 1 秒的等待时间，可以根据需要调整

# 多个人的问题
questions = [
    "What is the meaning of life?",
    "How does the universe work?",
    "Can you tell me a joke?",
    # # 可以添加更多的问题
]

# 使用生成器逐个生成回复
responses_generator = generate_responses(questions)

# 处理每个人的回复
for question, response in zip(questions, responses_generator):
    print(f"Question: {question}")
    print(f"Response: {response}")
    print()
