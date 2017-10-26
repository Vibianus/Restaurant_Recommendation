#coding:utf-8
import socket, sys
import json

class Connect:

    def __init__(self):
        self.json_dict = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #self.json_dict = {}
    # type :
    # R for Recommend
    # U for assign new preference( restaurant )
    # A for add new user

    def set_ip(self) :
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('140.116.247.172', 2087))

    def recommend_request( self, name, location ):
        self.set_ip()
        self.json_dict['type'] = 'R'
        self.json_dict['user'] = name
        self.json_dict['location'] = location
        json_item = json.dumps(self.json_dict)
        self.sock.send(json_item.encode('utf-8'))
        item = self.sock.recv(262144)
        self.sock.close()
        return json.loads(item.decode('utf-8'))

    def update_preference( self, name, key, like ):
        self.set_ip()
        self.json_dict['type'] = 'U'
        self.json_dict['user'] = name
        self.json_dict['restaurant_id'] = key
        self.json_dict['record'] = like
        json_item = json.dumps(self.json_dict)
        self.sock.send(json_item.encode('utf-8'))
        item = self.sock.recv(262144)
        self.sock.close()
        return json.loads(item.decode('utf-8'))

    def add_user( self, name ):
        self.set_ip()
        self.json_dict['type'] = 'A'
        self.json_dict['user'] = name
        json_item = json.dumps(self.json_dict)
        self.sock.send(json_item.encode('utf-8'))
        item = self.sock.recv(262144)
        self.sock.close()
        return json.loads(item.decode('utf-8'))

    def calculate_new_user_vector( self, name ):
        self.set_ip()
        self.json_dict['type'] = 'C'
        self.json_dict['user'] = name
        json_item = json.dumps(self.json_dict)
        self.sock.send(json_item.encode('utf-8'))
        item = self.sock.recv(262144)
        self.sock.close()
        return json.loads(item.decode('utf-8'))

    #json_item = add_user('洪梓軒66666')
    #json_item = recommend_request('洪梓軒66666', '22.997689, 120.221135')
    #json_item = update_preference( '洪梓軒66666', "ChIJV6k7LJt2bjQR89A0zSlFmXo", 'Y' )
    #json_item = calculate_new_user_vector('洪梓軒666')
    #json_item = calculate_new_user_vector( '洪梓軒66666' )
