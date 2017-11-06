#coding:utf-8
import os
import sys
import json
import client
import template_json
import requests
from datetime import datetime
from send_msg import sendtofb
import requests
from flask import Flask, request

app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message
                    print('testtesttest')
                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID

                    if "attachments" in messaging_event["message"] :
                        for attachment in messaging_event["message"]["attachments"] :
                            if "payload" in attachment and "coordinates" in attachment["payload"] :
                                location = attachment["payload"]["coordinates"]
                                check = connect_server( sender_id, 'A', location=location)
                                print(str(check))
                                reply = "已記錄位置資訊😀   日後想更改位置可以再次傳送位置給我~"
                                send_message( sender_id, reply )
                        break

                    if "text" in messaging_event["message"] :
                        message_text = messaging_event["message"]["text"]  # the message's text
                        message_text = message_text.encode('utf-8').lower()

                        reply = handle_message( message_text, sender_id )

                        if type(reply) == str :
                            send_message( sender_id, reply )
                        else : #template
                            send_template_message( reply )
                        pass

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["postback"]["payload"]  # the message's text
                    message_text = message_text.encode('utf-8')
                    if message_text == "<GET_STARTED_PAYLOAD>" : # first time get location
                        reply = first_use( sender_id )
                        send_template_message( reply )
                    else : #update personal preference
                        reply = handle_feedback( message_text, sender_id )
                        send_message( sender_id, reply )

    return "ok", 200


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message":{
            "text": message_text
        }
    })
    sendtofb(data)

def send_template_message(reply):
    data = json.dumps(reply.template)
    sendtofb(data)


def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()

def handle_feedback(message_text, recipient_id):
        rec_result = connect_server( recipient_id, 'U', restaurant_id=message_text[1:], record=message_text[0])
        print(rec_result)
        if message_text[0] == 'Y' : return '😀 已更新您的喜好'
        if message_text[0] == 'N' : return '😓 已更新您的喜好'

def first_use( recipient_id ):
        get_location = template_json.Template_json(recipient_id,template_type=4)
        return get_location


def handle_message(message_text, recipient_id):

    if u'有空'.encode("utf8") in message_text or u'閒'.encode("utf8") in message_text :
        return '要作什麼呢?'

    if u'出門'.encode("utf8") in message_text :
        return '外面天氣怎麼樣呢?'

    if u'早安'.encode("utf8") in message_text :
        return '早安!'

    if u'天氣'.encode("utf8") in message_text :
        if u'雨'.encode("utf8") in message_text :
            return '下雨路上濕滑，騎車的話要小心!'
        if u'糟'.encode("utf8") in message_text or u'不好'.encode("utf8") in message_text or u'不太好'.encode("utf8") in message_text :
            return '好的 出門要注意安全喔 🙂'
        if u'不錯'.encode("utf8") in message_text or u'普通'.encode("utf8") in message_text or u'可以'.encode("utf8") in message_text or u'好'.encode("utf8") in message_text :
            return '好的 一路順風 🙂'

    if u'不舒服'.encode("utf8") in message_text or u'感冒'.encode("utf8") in message_text :
        return '多多休息，要記得看醫生喔'

    if u'餐廳'.encode("utf8") in message_text or u'吃飯'.encode("utf8") in message_text or u'吃的'.encode("utf8") in message_text or u'吃什麼'.encode("utf8") in message_text or u'午餐'.encode("utf8") in message_text or u'晚餐'.encode("utf8") in message_text:
        rec_result = connect_server( recipient_id, 'R')
        restaurant = template_json.Template_json(recipient_id,template_type=1)
        for item in rec_result :
            if 'chinese_type' in item :
                restaurant.addItem( item['title'], item['picture'], item['res_key'], item['chinese_type'] + '  ' +item['address'])
            else :
                restaurant.addItem( item['title'], item['picture'], item['res_key'], item['address'])
        return restaurant

    return '😵😵不太懂剛剛的話呢'

def connect_server( recipient_id, conn_type, restaurant_id=None, record=None, location=None):
    json_dict = {}
    json_dict['type'] = conn_type
    #json_dict['user'] = '洪梓軒66666'
    json_dict['user'] = recipient_id
    if location : json_dict['location'] = location
    if restaurant_id : json_dict['restaurant_id'] = restaurant_id
    if record : json_dict['record'] = record
    json_item = json.dumps(json_dict)

    r = requests.get('http://140.116.247.172:8888', data=json_item.encode('utf-8')).content
    return json.loads(r.decode('utf-8'))




if __name__ == '__main__':
    app.run(debug=True)
