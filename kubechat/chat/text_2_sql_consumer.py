from channels.generic.websocket import WebsocketConsumer


class Text2SQLConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data, **kwargs):
        self.send(text_data=text_data)

