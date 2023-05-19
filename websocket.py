from .core import *
from websockets.server import serve
import asyncio

_proxies = {}
async def listen(addr:str, port:int, proxies = {}):
    _proxies.update(proxies)
    async with serve(handler, addr, port):
        await asyncio.Future()

async def handler(socket):
    _cookie = None
    ai = None

    def event_sender(e):
        e.update({'type':'event'})
        asyncio.run(socket.send(tojson(e)))

    async for payload in socket:
        message = json.loads(payload)
        cookie = message.get('cookie')
        if cookie:
            _cookie = cookie
            ai = AI(Model(_cookie, dict.fromkeys(events, event_sender), _proxies))
        if not ai:
            await socket.send('{"type":"error", "message":"model is not initialized"}')
        context = message.get('context')
        prompt = message.get('prompt')
        try:
            async for chunk in ai.exec({
                'context': context,
                'prompt': prompt,
            }):
                await socket.send(tojson({'type':'message', 'message': chunk}))
        except Exception as e:
            await socket.send(tojson({'type':'error', 'message': errString(e)}))

    await ai.close()