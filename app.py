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

taiwan_location = ['臺北', '台北', '新北', '桃園', '臺中', '台中', '臺南', '台南', '高雄',
                    '新竹', '嘉義', '苗栗', '彰化', '南投', '雲林','屏東', '宜蘭', '花蓮', '台東', '臺東']

global_stat = {}


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
    global global_stat

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message
                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID

                    if "attachments" in messaging_event["message"] :
                        for attachment in messaging_event["message"]["attachments"] :
                            if "payload" in attachment and "coordinates" in attachment["payload"] :
                                location = attachment["payload"]["coordinates"]
                                check = connect_server( sender_id, 'A', location=location)

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
                            rec_reply = "推薦您" + str(global_stat['location']) + str(global_stat['time']) + "的餐廳"
                            send_message( sender_id, rec_reply )
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
                    if message_text == "<GET_STARTED_PAYLOAD>" : # first time get location & set status
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

    if message_text[0] == 'Y' : return '😀 已更新您的喜好'
    if message_text[0] == 'N' : return '😓 已更新您的喜好'

def first_use( recipient_id ):
    get_location = template_json.Template_json(recipient_id,template_type=4)
    status = dict()
    status['time'] = ''
    status['location'] = ''
    status['intent'] = 'N'
    change_status = connect_server( recipient_id, 'S', status=status )
    log(change_status['result'])
    return get_location

def check_time_and_location(message_text, stat):
    if u'晚上'.encode("utf8") in message_text or u'晚餐'.encode("utf8") in message_text :
        stat['time'] = 'night'
    elif u'中午'.encode("utf8") in message_text or u'午餐'.encode("utf8") in message_text :
        stat['time'] = 'noon'
    elif u'早上'.encode("utf8") in message_text or u'早餐'.encode("utf8") in message_text :
        stat['time'] = 'morning'

    if u'這附近'.encode("utf8") in message_text or u'這邊'.encode("utf8") in message_text :
        stat['location'] = 'here'
    else :
        for location in taiwan_location :
            if location in message_text : stat['location'] = location

    return stat

def check_stat_and_recommend(message_text, stat_result, recipient_id):
    global global_stat
    stat_result['result'] = check_time_and_location(message_text, stat_result['result'])
    change_status = connect_server( recipient_id, 'S', status=stat_result['result'] )
    if stat_result['result']['location'] == '' and stat_result['result']['time'] == '' :
        return '請問在什麼時間地點吃呢?😀'
    elif stat_result['result']['time'] == '' :
        return '請問是什麼時間吃呢?😀'
    elif stat_result['result']['location'] == '' :
        return '請問在哪裡吃呢?😀'
    else :

        rec_result = connect_server( recipient_id, 'R')
        restaurant = template_json.Template_json(recipient_id,template_type=1)
        for item in rec_result :
            if 'chinese_type' in item :
                restaurant.addItem( item['title'], item['picture'], item['res_key'], item['chinese_type'] + '  ' +item['address'])
            else :
                restaurant.addItem( item['title'], item['picture'], item['res_key'], item['address'])

        #change global_stat & intent
        global_stat['time'] = stat_result['result']['time']
        global_stat['location'] = stat_result['result']['location']

        stat_result['result']['intent'] = 'N'
        stat_result['result']['time'] = ''
        stat_result['result']['location'] = ''
        change_status = connect_server( recipient_id, 'S', status=stat_result['result'] )
        return restaurant


# def rec_procedure( message_text, recipient_id ):
#     if u'早餐'.encode("utf8") in message_text or u'早上'.encode("utf8") in message_text :


def handle_message(message_text, recipient_id):

    stat_result = connect_server( recipient_id, 'F' )

    if 'intent' in stat_result['result'] :
        if stat_result['result']['intent'] == 'Y' :
            return check_stat_and_recommend(message_text, stat_result, recipient_id)


    if u'餐廳'.encode("utf8") in message_text or u'吃飯'.encode("utf8") in message_text or u'吃的'.encode("utf8") in message_text or u'吃什麼'.encode("utf8") in message_text :
        #change intent
        if 'intent' in stat_result['result'] :
            stat_result['result']['intent'] = 'Y'
            change_status = connect_server( recipient_id, 'S', status=stat_result['result'] )

            return check_stat_and_recommend(message_text, stat_result, recipient_id)

    if u'有空'.encode("utf8") in message_text or u'閒'.encode("utf8") in message_text :
        return '要作什麼呢?'

    if u'出門'.encode("utf8") in message_text :
        return '外面天氣怎麼樣呢?'

    if u'早安'.encode("utf8") in message_text :
        return '早安!'

    if u'你好'.encode("utf8") in message_text :
        return '你好r'

    if u'天氣'.encode("utf8") in message_text :
        if u'雨'.encode("utf8") in message_text :
            return '下雨路上濕滑，騎車的話要小心!'
        if u'糟'.encode("utf8") in message_text or u'不好'.encode("utf8") in message_text or u'不太好'.encode("utf8") in message_text :
            return '好的 出門要注意安全喔 🙂'
        if u'不錯'.encode("utf8") in message_text or u'普通'.encode("utf8") in message_text or u'可以'.encode("utf8") in message_text or u'好'.encode("utf8") in message_text :
            return '好的 一路順風 🙂'

    if u'不舒服'.encode("utf8") in message_text or u'感冒'.encode("utf8") in message_text :
        return '多多休息，要記得看醫生喔'



    return '😵😵不太懂剛剛的話呢'

def connect_server( recipient_id, conn_type, restaurant_id=None, record=None, location=None, time=None, status=None):
    json_dict = {}
    json_dict['type'] = conn_type
    #json_dict['user'] = '洪梓軒66666'
    json_dict['user'] = recipient_id
    if location : json_dict['location'] = location
    if restaurant_id : json_dict['restaurant_id'] = restaurant_id
    if record : json_dict['record'] = record
    if status : json_dict['status'] = status
    json_item = json.dumps(json_dict)

    r = requests.get('http://140.116.247.172:8888', data=json_item.encode('utf-8')).content
    log( 'gotjson : ' + str(r))
    return json.loads(r.decode('utf-8'))




if __name__ == '__main__':
    app.run(debug=True)
