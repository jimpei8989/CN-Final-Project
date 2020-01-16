import os, sys, time, datetime, logging
import signal
import json
import socket, selectors
from threading import Thread

from constants import *
from backend.userManagement import AccountAgent
from backend.chatroomManagement import ChatroomManager
from backend.misc import createLogger 

class Server():
    def __init__(self, hostname = 'localhost', port = 2900, dataDir = os.path.join('server-data')):
        self.logger = createLogger('server')

        # Create directories
        if not os.path.isdir(dataDir):
            os.mkdir(dataDir, mode = 0o0711)
            self.logger.info(f'Create data directory `{dataDir}`')

        chatroomDir = os.path.join(dataDir, 'chatrooms')
        if not os.path.isdir(chatroomDir):
            os.mkdir(chatroomDir, mode = 0o0711)
            self.logger.info(f'Create data directory `{chatroomDir}`')

        # Load Account Agent
        self.accountAgent = AccountAgent(dataDir)
        self.accountAgent.load()

        # Load Chatroom Agent
        self.chatroomMgr = ChatroomManager(chatroomDir)
        self.chatroomMgr.load()

        # Socket - create and bind
        for trials in range(10):
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.bind((hostname, port))
                self.sock.setblocking(0)
            except socket.error as msg:
                self.logger.info(f'✘ [Init Server Socket] : {msg}')
                time.sleep(1)
            else:
                self.logger.info('✓ [Init Server Socket]')
                return 
        exit(-1)
    def saveall(self):
        self.accountAgent.save()
        self.chatroomMgr.save()

    def handleConnection(self, data, clientSocket, clientIP, clientPort, connectionState):
        def sendOK(msg = ''):
            clientSocket.send(('OK' if msg == '' else f'OK|{msg}').encode('UTF-8'))
        def sendFail(msg = ''):
            clientSocket.send(('Fail' if msg == '' else f'Fail|{msg}').encode('UTF-8'))

        def getUser():
            if clientSocket not in connectionState or connectionState[clientSocket] is None:
                sendFail('Please login first')
                return None
            else:
                return connectionState[clientSocket][0]

        # TODO: Handle Registration (DONE)
        if data['type'] == 'Register':
            if clientSocket in connectionState and connectionState[clientSocket] is not None:
                self.logger.info('handleConnection -> Register: Please logout first')
                return
            username, password = data['username'], data['password']
            result = self.accountAgent.createUser(username, password)
            if result == True:
                sendOK()
                self.logger.info(f'handleConnection -> Register: \'{username}\' created successfully')
            else:
                msg = result[1]
                sendFail(msg)
                self.logger.info(f'handleConnection -> Register: \'{username}\' fail ({msg})')

        # TODO: Handle Login (DONE)
        if data['type'] == 'Login':
            if clientSocket in connectionState and connectionState[clientSocket] is not None:
                self.logger.info('handleConnection -> Login: You\'ve already login')
                sendFail('Please logout first')
                return
            username, password = data['username'], data['password']
            result = self.accountAgent.verifyUser(username, password)
            if result == True:
                connectionState[clientSocket] = username, 'Login'
                sendOK()
                self.logger.info(f'handleConnection -> Login: \'{username}\' login from [{clientIP}:{clientPort}]')
            else:
                msg = result[1]
                sendFail(msg)
                self.logger.info(f'handleConnection -> Login: \'{username}\' fail ({msg})')

        # TODO: Create Chatroom (DONE)
        if data['type'] == 'CreateChatroom':
            user = getUser()
            if user is not None:
                name, icon, admins, members = data['name'], data['icon'], data['admins'], data['members']
                ret = self.chatroomMgr.createChatroom(name, icon, admins + [user], members + [user])
                if ret is True:
                    self.accountAgent.addUsersToChatroom(admins + members + [user], name)
                    self.logger.info(f'handleConnection -> CreateChatroom: chatroom {name} created by \'{user}\' successfully')
                    sendOK()
                else:
                    sendFail(ret[1])

        # TODO: Get User Chatrooms
        if data['type'] == 'GetChatroomList':
            user = getUser()
            chatroomList = self.accountAgent.getChatroomList(user)
            chatroomList = sorted([self.chatroomMgr.getMetadata(c) for c in chatroomList], key = lambda k : k[2], reverse = True)
            print(json.dumps(chatroomList))
            sendOK(json.dumps(chatroomList))
            self.logger.info(f'handleConnection -> GetUserChatroomList: user \'{user}\' queried successfully')
            
        # TODO: Change name / Change icon

        # TODO: Make Admin / Make normal

        # TODO: Add member / Kick member

        # TODO: Get Chat History
        if data['type'] == 'GetChatHistory':
            user = getUser()
            name, size = data['name'], data['size'] if 'size' in data else 1000
            if name not in self.chatroomMgr.chatrooms:
                sendFail('Query chatroom name wrong')
            elif not self.chatroomMgr.chatrooms[name].isMember(user):
                sendFail('Permission Error')
            else:
                history = self.chatroomMgr.chatrooms[name].getChatHistory(size)
                print(history)
                sendOK(json.dumps(history))
                self.logger.debug(f'handleConnection -> GetChatHistory: \'{user}\' queried chatroom')

        # TODO: Handle Messaging
        if data['type'] == 'Messaging':
            user = getUser()
            name, text = data['name'], data['text']
            if name in self.chatroomMgr.chatrooms and self.chatroomMgr.chatrooms[name].isMember(user):
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                userIcon = self.accountAgent.getUserIcon(user)
                self.chatroomMgr.chatrooms[name].addChat(user, userIcon, text, timestamp)
                sendOK()
                self.logger.debug(f'handleConnection -> Messaging: \'{user}\' texted\n\t\t\t{text}\n\t\tin [{name}]')
            else:
                sendFail('Permission Error')

        # TODO: Handle Upload File
        if data['type'] == 'UploadFile':
            user = getUser()
            name, filename, content = data['name'], data['filename'], data['content']
            if name in self.chatroomMgr.chatrooms and self.chatroomMgr.chatrooms[name].isMember(user):
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.chatroomMgr.chatrooms[name].addFile(sender, None, filename, content, timestamp)
                sendOK()
                self.logger.debug(f'handleConnection -> UploadFile: \'{user}\' texted\n\t\t\t{text}\n\t\tin [{name}]')
            else:
                sendFail('Permission Error')

        # TODO: Handle Download File
        if data['type'] == 'DownloadFile':
            user = getUser()
            name, filename= data['name'], data['filename']
            if name in self.chatroomMgr.chatrooms and self.chatroomMgr.chatrooms[name].isMember(user):
                content = self.chatroomMgr.chatrooms[name].getFile(filename)
                if content is None:
                    sendFail('File not found')
                else:
                    sendOK(content)
            else:
                sendFail('Permission Error')

        if data['type'] == 'UpdateIcon':
            user = getUser()
            icon = data['icon']
            self.accountAgent.setUserIcon(user, icon)
            sendOK()

    def start(self, timeout = None, maxNumOfConnections = 1024):
        self.sock.listen(maxNumOfConnections)
        beginTimestamp = time.process_time()
        connectionState = dict()    # socket -> (user, state)

        # Selector
        selector = selectors.DefaultSelector()
        selector.register(self.sock, selectors.EVENT_READ, data = None)

        while timeout is None or time.process_time() - beginTimestamp < timeout:
            events = selector.select(timeout = None)
            for key, mask in events:
                if key.data is None:
                    connection, address = self.sock.accept()
                    connection.setblocking(0)
                    selector.register(connection, selectors.EVENT_READ | selectors.EVENT_WRITE, data = address)
                    clientIP, clientPort = address
                    self.logger.info(f'Connection from [{clientIP} : {clientPort}]')
                else:
                    self.logger.debug(f'RECV from [{clientIP}:{clientPort}]')
                    connection = key.fileobj
                    if mask & selectors.EVENT_READ:
                        try:
                            iptBytes = connection.recv(MAX_BUFFER_SIZE)
                            if iptBytes:
                                data = json.loads(iptBytes.decode('utf-8')) # A string
                                print(f'{data}')
                                newThread = Thread(target = self.handleConnection,
                                                   args = (data, connection, clientIP, clientPort, connectionState)
                                                   )
                                newThread.run()
                            else:
                                self.logger.warning(f'Connection lost by [{clientIP} : {clientPort}]')
                                selector.unregister(connection)
                                if connection in connectionState:
                                    del connectionState[connection]
                        except ConnectionResetError:
                            self.logger.warning(f'Connection reset by [{clientIP} : {clientPort}]')
                            selector.unregister(connection)
                            if connection in connectionState:
                                del connectionState[connection]
                        except json.decoder.JSONDecodeError:
                            print(iptBytes)
                            self.logger.warning(f'JSON Decodes error')

        self.sock.close()

def main():
    # TODO: server config
    server = Server()

    def handler(signum, frame):
        # TODO: saveall
        server.saveall()
        exit(0)

    signal.signal(signal.SIGINT, handler)

    server.start()


if __name__ == '__main__':
    main()

