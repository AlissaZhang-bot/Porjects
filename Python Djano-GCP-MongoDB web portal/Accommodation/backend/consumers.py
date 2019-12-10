##====================================================================
# Same as view.py, however view is the main backend for http protocal,
# this file used for ASGI
##====================================================================

from channels.generic.websocket import WebsocketConsumer
from .chatbot import service, workspace_id
import json

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['data']
        response = service.message(
            workspace_id = workspace_id,
            input = {'text': message}).get_result()
        response_message = ''.join(response['output']['text'])
        print(response_message)
        self.send(text_data=json.dumps({
            'data': response_message
        }))