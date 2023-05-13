import json
from random import randint
from time import sleep
import requests
import sseclient

# For channels
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer

xano_base_url = 'https://xl2o-hsyi-mgjy.n7.xano.io/api:F1Ka7HkO/'


class WSConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        print('is connected')
        self.scope["cookies"].get("stopWs")
        # for i in range(1, 1000):
        #     num = i
        #     self.send(json.dumps({'message': i}))

    def receive(self, text_data=None, bytes_data=None):
        answer = ''
        data = json.loads(text_data)
        dialogues = data['dialogues']
        chat_id = data['chat_id']
        completion_key = data['completion_key']

        # 验证 completion_key
        data = {
            'chat_id': chat_id,
            'completion_key': completion_key
        }
        url = xano_base_url + 'dialogue/verify_completion_key'
        response = requests.post(url, data=data)
        try:
            openai_key = response.json()['openai_key']
        except:
            print('验证失败')
            self.send(json.dumps({
                'message': '发生错误,对话额度已退回您的账户'
            }))
            self.disconnect(1)
            return

        # 验证成功
        print('验证成功')
        # 开始生成回复
        messages = [
            {
                "role": "system",
                "content": "你是一个AI助手，你会用markdown格式回复用户。"
            }

        ]
        for dialogue in dialogues:
            sender_is_bot = dialogue['sender_is_bot']
            content = dialogue['content']
            print(content)
            if sender_is_bot:
                role = 'assistant'
            else:
                role = 'user'
            messages.append({
                "role": role,
                "content": content
            })
        print(messages)
        url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + openai_key
        }
        body = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "temperature": 0.7,
            "stream": True,
        }
        request = requests.post(url, stream=True, headers=headers, json=body)
        client = sseclient.SSEClient(request)
        for event in client.events():
            chunk = ''
            finished = False
            if event.data != '[DONE]':
                # print(event.data)
                try:
                    chunk = json.loads(event.data)['choices'][0]['delta']['content']
                    # print(chunk)
                except:
                    chunk = ''

                answer += chunk
            else:
                finished = True

            self.send(json.dumps({
                'answer': answer,
                'chunk': chunk,
                'finished': finished,
            }))

        if len(answer) == 0:
            # 发生错误
            # 归还算力
            url = xano_base_url + 'dialogue/reverse'
            data = {
                'completion_key': completion_key,
                'credential': 'wfhuwh23786s9fuoi21/jdsfisiji18'
            }
            requests.post(url, data=data)
            self.send(json.dumps({
                'message': '发生错误,对话额度已退回您的账户'
            }))
        self.disconnect(1, answer)

    def disconnect(self, code, answer=None, completion_key=None):
        self.send(json.dumps({
            'message': 'disconnect'
        }))
        print('disconnect!!!')
        print(code)
        print(answer)
