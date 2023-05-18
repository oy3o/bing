from .core import *
from websockets.server import serve
import asyncio

async def listen(addr:str, port:int):
    async with serve(handler, addr, port):
        await asyncio.Future()

clients = {}
async def handler(socket):
    _cookie = None
    _model = None

    def event_sender(e):
        e.update({'type':'event'})
        asyncio.run(socket.send(tojson(e)))
    async for payload in socket:
        message = json.loads(payload)
        cookie = message.get('cookie')
        if cookie and (cookie != _cookie):
            _cookie = cookie
            _model = Model(_cookie, dict.fromkeys(events, event_sender),{
                'http://': 'http://win.local:1081',
                'https://': 'http://win.local:1081',
            })
        if not _model:
            await socket.send('{"type":"error", "message":"model is not initialized"}')
        context = message.get('context')
        prompt = message.get('prompt')
        try:
            async for chunk in _model.exec({
                'context': context,
                'prompt': prompt,
            }):
                await socket.send(tojson({'type':'message', 'message': chunk}))
        except Exception as e:
            await socket.send(tojson({'type':'error', 'message': errString(e)}))