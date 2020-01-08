import os, sys, time, logging
import json
import socket, ssl
from getpass import getpass

from constants import *

class Client():
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = None

    def connect(self, hostname = 'localhost', port = 2900):
        self.sock.connect((hostname, port))

    def send(self, message):
        self.sock.send(message.encode('utf-8'))

    def recv(self):
        return self.sock.recv(MAX_BUFFER_SIZE).decode('UTF-8')

    def register(self):
        print('=== Register ===')
        username = input('Username: ')
        password = getpass()
        data = {'type' : 'Register', 'username' : username, 'password' : password}
        self.send(json.dumps(data))
        msg = self.recv()

    def login(self):
        print('==== Login ====')
        username = input('Username: ')
        password = getpass()
        data = {'type' : 'Login', 'username' : username, 'password' : password}
        self.send(json.dumps(data))
        msg = self.recv()
        if 'OK' in msg:
            self.username = username
        return 'OK' in msg

    def createChatroom(self):
        name = input('Chatroom Name: ')
        people = input('Talking With: ').split(', ')[0]
        data = {'type' : 'CreateChatroom', 'name' : name, 'admins' : [self.username, people], 'members' : [self.username, people]}
        self.send(json.dumps(data))
        msg = self.recv()
        ID = msg.split('|')[1]
        return ID

    def getChatroomList(self, verbose = True):
        data = {'type' : 'GetChatroomList'}
        self.send(json.dumps(data))
        msg = self.recv()
        self.chatroomList = set(sorted(json.loads(msg.split('|')[1])))
        if verbose:
            os.system("clear")
            print('### Chatroom List ###')
            print('\n'.join(ID for ID in self.chatroomList))
            print('#####################')

    def getChatHistory(self, ID):
        data = {'type' : 'GetChatHistory', 'ID' : ID}
        self.send(json.dumps(data))
        msg = self.recv()
        history = json.loads(msg.split('|')[1])
        os.system("clear")
        for chat in history:
            print(f'''{chat['sender']} ({chat['timestamp'].split(' ')[1]}): {chat['text']}''')

    def chat(self, ID):
        text = input(f'{self.username}> ')
        data = {'type' : 'Messaging', 'ID' : ID, 'text' : text}
        self.send(json.dumps(data))
        msg = self.recv()

def main():
    # Set self.logger config
    logging.basicConfig(filename = 'client.log',
                        filemode = 'w',
                        )

    client = Client()
    client.connect()

    while True:
        if input('Register? [yn]: ') == 'y':
            client.register()
            break
        else:
            break

    while True:
        result = client.login()
        if result == True:
            break
        if input('Login Again? [yn]: ') != 'y':
            return

    client.getChatroomList()
    while True:
        cr = input("Enter which chatroom (Type 'create' to create a new one): ")
        if cr == 'create':
            ID = client.createChatroom()
            client.getChatroomList(False)
        else:
            client.getChatHistory(cr)
            break
    while True:
        client.chat(cr)
        client.getChatHistory(cr)

if __name__ == '__main__':
    main()

