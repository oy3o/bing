from oy3opy.utils.string import random_hex, tojson
from oy3opy.utils.task import Task
from oy3opy.ai.model import AI, Model as _Model
import certifi
import httpx
import json
import random
import ssl
import uuid
from websockets.client import connect

events = ['error','create','update','send','generate','result','reply_suggestion','search','search_result','revoke','max_revoke','max_invocation']

ssl_context = ssl.create_default_context()
ssl_context.load_verify_locations(certifi.where())

Microsoft_IP = f'13.{random.randint(104, 107)}.{random.randint(0, 255)}.{random.randint(0, 255)}'

RequestHeader = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    'cache-control': 'no-cache', 
    'pragma': 'no-cache', 
    'referrer': 'https://edgeservices.bing.com/edgesvc/chat?udsframed=1&form=SHORUN&clientscopes=chat,noheader', 
    'referrer-policy': 'origin-when-cross-origin', 
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-ms-client-request-id": str(uuid.uuid4()),
    "x-forwarded-for": Microsoft_IP,
}

class Request:
    def __init__(self, data, page):
        self.client_id: str = data['clientId']
        self.conversation_id: str = data['conversationId']
        self.conversation_signature: str = data['conversationSignature']
        self.state = data['result']
        self.page = page
    def update(self, context):
        self.page = {
            'author': 'oy3o', 
            'description': context, 
            'contextType': 'WebPage', 
            'messageType': 'Context', 
            'sourceName': '❤️', 
            'sourceUrl': 'https://oy3o.com/❤️'
        }
        return {
            'conversationId': self.conversation_id,
            'conversationSignature': self.conversation_signature,
            'messages': [self.page],
            'participant': {'id': self.client_id},
            'source': "cib",
            'traceId': random_hex(32),
        }
    def message(self, id, text):
        struct = {
            'arguments': [
                {
                    'source': 'cib', 
                    'optionsSets': [
                            'nlu_direct_response_filter', 'deepleo', 'disable_emoji_spoken_text', 'enablemm', 'h3imaginative', 'gencontentv3', 'alllanguages', 'dlreldeav1', 
                            'rediscluster', 'travelansgnd', 'gencontentv5', 'e2ecachewrite', 'cachewriteext', 'dagslnv1', 'dv3sugg', 'knowimg', 'videoansgnd'], 
                    'allowedMessageTypes': ['ActionRequest', 'Chat', 'Context', 'InternalSearchQuery', 'InternalSearchResult', 'InternalLoaderMessage', 'RenderCardRequest', 
                            'SemanticSerp', 'GenerateContentQuery', 'SearchQuery'], 
                    'sliceIds': ['0329resps0', '0417redis', '0427visual_b', '420bic', '420deav1', '420langdsat', '4252tfinances0', '425bicp2', '427startpms0', '427vserps0', 
                            '430rai267s0', '505iccrics0', '508jbcars0', '512biccp1', '522docxfmts0', '0524txt4', 'bcsr', 'clarityconvcf', 'convcssasync', 'convcssclick', 'creatgoglt', 'creatorv2t', 
                            'disablechatsupp', 'dtvoice2', 'forallv2', 'forallv2pc', 'kcentnam', 'kcimgattcf', 'mbssrrsuppr', 'mlchat7bml', 'mlchat8k', 'norespwtf', 'qachatmb-c', 'sacf', 'sbsvgoptcf', 'scprompt2', 
                            'ssoverlap0', 'ssoverlap25', 'sspltop5', 'ssrrcache', 'tempcacheread', 'temptacache', 'ttstmout', 'ttstmoutcf', 'v2basetag', 'workpayajax'], 
                    'traceId': random_hex(32), 
                    'verbosity': 'verbose', 
                    'isStartOfSession': id == 0, 
                    'message': {
                        'locale': 'zh-CN', 
                        'market': 'zh-CN', 
                        'region': 'US', 
                        'location': 'lat:0;long:0;re=0m;', 
                        'locationHints': [{
                                'country': 'oy3o', 
                                'state': 'oy3o', 
                                'city': 'oy3o', 
                                'zipcode': '000000', 
                                'timezoneoffset': 0, 
                                'countryConfidence': 0, 
                                'Center': {'Latitude': 0, 'Longitude': 0}, 
                                'RegionType': 0, 
                                'SourceType': 0
                            }], 
                        'author': 'user', 
                        'inputMethod': 'Keyboard', 
                        'text': text, 
                        'messageType': 'Chat'
                    }, 
                    'conversationSignature': self.conversation_signature, 
                    'participant': {'id': self.client_id}, 
                    'conversationId': self.conversation_id
            }], 
            'invocationId': str(id), 
            'target': 'chat', 
            'type': 4,
        }
        if not id and self.page:
            struct['arguments'][0]['previousMessages'] = [self.page]
        return tojson(struct) + '\x1e'

class Model(_Model):# cookie, proxies, chat, context
    def init(self):
        with httpx.Client(
            headers=RequestHeader, 
            proxies=self.proxies, 
            timeout=16,
            transport=httpx.HTTPTransport(retries=3), 
            cookies=self.cookie,
        ) as client:
            response = client.get('https://edgeservices.bing.com/edgesvc/turing/conversation/create')
            if response.status_code != 200:
                raise f'code:{response.status_code}\ntext:{response.text}'
            self.info = response.json()
            self.request = Request(self.info, self.context)
            if self.request.state['value'] != 'Success':
                raise self.request.state['result']['message']
        self.invocation_max = -1
        self.invocation_id = 0
        self.revoke_times = 0
        self.trigger('create', {'message': self.info})

    async def update(self, context):
        if not self.invocation_id:
            self.request.update(context)
            return

        with httpx.Client(
            headers=RequestHeader, 
            proxies=self.proxies, 
            timeout=16,
            transport=httpx.HTTPTransport(retries=3),
        ) as client:
            response = client.post(
                'https://sydney.bing.com/sydney/UpdateChat',
                json=self.request.update(context),
            )
            if response.status_code != 200:
                raise f'code:{response.status_code}\ntext:{response.text}'
        self.trigger('update', {'message': context})

    async def send(self, message):
        async with connect('wss://sydney.bing.com/sydney/ChatHub',extra_headers=RequestHeader,max_size=None,ssl=ssl_context) as wss:
            await wss.send('{"protocol":"json", "version":1}\x1e')
            await wss.recv()

            await wss.send(self.request.message(self.invocation_id, message))
            self.trigger('send', {'message': message})

            last = ''
            final = False
            while self.chat and not final:
                try: frame = await wss.recv()
                except: frame = await wss.recv()
                payloads = str(frame).split('\x1e')
                for payload in payloads:
                    if not payload:
                        continue
                    try:
                        msg = json.loads(payload)
                    except:
                        self.error('receive', payload)
                    err = msg.get('error')
                    if err:
                        self.error('receive', err)
                    elif msg['type'] == 1:
                        # update turn count
                        throttling = msg['arguments'][0].get('throttling')
                        if throttling:
                            self.invocation_max = throttling['maxNumUserMessagesInConversation']
                            self.invocation_id = throttling['numUserMessagesInConversation']
                        # filter apology
                        messages = msg['arguments'][0].get('messages')
                        if (not messages) or (messages[0]['contentOrigin'] == 'Apology'):
                            continue
                        # deal with message
                        message = messages[0]
                        mtype = message.get('messageType')
                        if (mtype == 'InternalLoaderMessage') or (mtype == 'RenderCardRequest'):
                            continue
                        elif (mtype == 'InternalSearchQuery'):
                            self.trigger('search', {'message': message['hiddenText']})
                        elif mtype == 'GenerateContentQuery':
                            self.trigger('generate', {'message': message['text']})
                        elif mtype == 'InternalSearchResult':
                            self.trigger('search_result', {'message': json.loads(message['hiddenText'][8:-3])['web_search_results']})
                        else:
                            chunk = message['text']
                            if not chunk:
                                continue
                            if chunk.startswith(last):
                                yield chunk[len(last):]
                                last = chunk
                            else:
                                yield chunk
                                last = chunk
                    elif msg['type'] == 2:
                        item = msg['item']
                        messages = item.get('messages')
                        if messages:
                            if messages[-1]['contentOrigin'] == 'Apology':
                                self.revoke_times += 1
                                self.trigger('revoke', {'message': message[-1]})
                            else:
                                suggestions = messages[-1].get('suggestedResponses')
                                if suggestions:
                                    self.trigger('reply_suggestion', {'message': [suggestion['text'] for suggestion in suggestions]})
                        if item.get('result') and item.get('result').get('message'):
                            self.trigger('result', {'message': item.get('result').get('message')})
                    elif msg['type'] == 3:
                        final = True

        if self.invocation_id == self.invocation_max:
            self.trigger('max_invocation',{'message': self.invocation_max})
            self.init()
            return
        if self.revoke_times == 3:
            self.trigger('max_revoke',{'message': self.revoke_times})
            self.init()

    async def close(self):
        pass
