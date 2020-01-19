import os
from sanic import Sanic
from sanic_restful import reqparse, Api, Resource
import requests
import json
from cryptography.fernet import Fernet
import base64

# Set global defines
API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHAT_USER_NAME = os.getenv("CHAT_USER_NAME")
DEBUG = bool(os.environ.get('DEBUG', ''))
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
PORT = int(os.environ.get("PORT", 8000))
WEB_CONCURRENCY = int(os.environ.get('WEB_CONCURRENCY', 1))

# setup sanic api engine
sanic = Sanic("__Sanic__")
sanic_errors = {
        'TypeError': {
            'status': 404,
            'message': 'not found'
            }
        }
api = Api(sanic, errors=sanic_errors)

parser = reqparse.RequestParser()
parser.add_argument('signature', location='form')
parser.add_argument('title', location='form')
parser.add_argument('text', location='form')

class SanicApiHandler(Resource):
    async def post(self, request):
        args = parser.parse_args(request);
        # validate signature
        if 'signature' in args:
            signature = self.decrypt_data(args['signature']).decode("utf-8")
            if signature == API_KEY:
                if 'title' in args and 'text' in args:
                    self.process_message(args['title'], args['text'])
        return {"ok": True}

    def process_message(self, title, message):
        self.send_message_to_bot(title, message)

    def decrypt_data(self, data):
        fernet = Fernet(ENCRYPTION_KEY)
        bytedata = base64.b64decode(data)
        return fernet.decrypt(bytedata)

    def send_message_to_bot(self, title, message):
        # decrypt the messages
        title_decr = self.decrypt_data(title).decode("utf-8") 
        text_decr = self.decrypt_data(message).decode("utf-8") 

        # setup telegram endpoint call
        endpoint = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
        payload = {
                    'chat_id': CHAT_ID,
                    'text': title_decr + ' :::: ' + text_decr 
                  }
        header = {
                    "Content-type": "application/x-www-form-urlencoded",
                    "Accept": "text/plain" 
                 }

        response = requests.post(endpoint, data=payload, headers=header)
        response_json = response.json()
        print(response_json)

# add endpoints
api.add_resource(SanicApiHandler, '/notify')

# Main function
if __name__ == '__main__':
    sanic.run(
        host='0.0.0.0',
        port=PORT,
        workers=WEB_CONCURRENCY,
        debug=DEBUG)
