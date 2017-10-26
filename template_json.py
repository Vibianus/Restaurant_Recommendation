#coding:utf-8
class Template_json :
    def __init__(self, sender_id, template_type, text=None, payload_yes=None, payload_no=None):
        self.text= text
        self.payload_yes = payload_yes
        self.payload_no = payload_no
        if template_type == 1 :
            self.template = {
                        "recipient": {
                        "id": sender_id
                        },
                        "message":{
                            "attachment":{
                                    "type":"template",
                                    "payload":{
                                                "template_type":"generic",
                                                "elements":[
                                                        ]
                                                }
                                        }
                                    }
                    }

        if template_type == 2:
            self.template ={
                "recipient":
                {
                    "id": sender_id
                },
                "message":
                {
                    "text": self.text,
                    "quick_replies": [
                        {
                            "content_type": "text",
                            "title": "是",
                            "payload": self.payload_yes
                        },
                        {
                            "content_type": "text",
                            "title": "否",
                            "payload": self.payload_no
                        }
                    ]
                }
            }
        if template_type == 3:
            self.template ={
                "recipient":
                {
                    "id": sender_id
                },
                "message":
                {
                    "text": self.text,
                    "quick_replies": [
                        {
                            "content_type": "text",
                            "title": "好喔",
                            "payload": self.payload_yes
                        },
                        {
                            "content_type": "text",
                            "title": "我剛剛按錯了",
                            "payload": self.payload_no
                        }
                    ]
                }
            }


    def addItem(self, title, image_url, feedback, address):
        bobble={
        "title":title,
        "image_url":image_url,
        "subtitle":address,
        "buttons":[
                    {
                        "type":"web_url",
                        "url":item_url,
                        "title":"View Website"
                    },{
                        "type":"postback",
                        "title":"Love It!",
						"payload": 'Y' + feedback
                    },{
                        "type":"postback",
                        "title":"Not Good...",
						"payload": 'N' + feedback
                    }
            ]
        }

        self.template["message"]["attachment"]["payload"]["elements"].append(bobble)
        return self.template
