from channels.generic.websocket import AsyncWebsocketConsumer

from django.core.cache import cache

# from .parser import total#, count_data, bad, good, check_again, again_domain, data, start_parser

import json
import asyncio

total = 0
class MyWSConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.send_message_task = asyncio.create_task(self.send_periodic_messages())
    
    async def disconnect(self, close_code):
        if hasattr(self, "send_message_task"):
            self.send_message_task.cancel()

    # async def receive(self, text_data):
    #     text_data_json = json.loads(text_data)
        
    #     await self.send(text_data=json.dumps({
    #         "msg": self.message
    #     }))
    #     self.message += 1
    #     await asyncio.sleep(5)

    async def send_periodic_messages(self):
        while True:
            # await self.send(text_data=json.dumps({"msg": self.message}))
            # self.message += 1
            if cache.get("start_parser"):
                print("total", cache.get("total"), cache.get("count_data"))
                percent = int(cache.get("total", 0) / cache.get("count_data", 1) * 100) 
                await self.send(text_data=json.dumps({"msg": percent}))
            else:
                await self.send(text_data=json.dumps({"msg": 0}))

            await asyncio.sleep(3)