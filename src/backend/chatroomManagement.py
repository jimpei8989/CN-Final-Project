import os
import json, pickle
import uuid
from backend.misc import createLogger

class Chatroom():
    def __init__(self, name, filename, icon = None, admins = set(), members = set()):
        self.name = name
        self.filename = filename
        self.icon = icon

        # Load
        self.admins = admins if type(admins) is set else set(admins)
        self.members = members if type(members) is set else set(members)
        self.chatHistory = []
        self.files = dict() # A dict filename -> base64 encoded files

    def __str__(self):
        return f'''
====== {self.name} ======
Icon: {self.icon}
Admins: {self.admins}
Members: {self.members}
chatHistory: {self.chatHistory}
files: {self.files}
'''[1:-1]

    def save(self):
        with open(self.filename, 'wb') as f:
            pickle.dump((self.icon, self.admins, self.members, self.chatHistory, self.files), f)

    def load(self):
        with open(self.filename, 'rb') as f:
            self.icon, self.admins, self.members, self.chatHistory, self.files = pickle.load(f)

    def isMember(self, user):
        return user in self.members or user in self.admins

    def isAdmin(self, user):
        return user in self.admins

    def getChatHistory(self, size = 1000):
        size = min(size, len(self.chatHistory))
        return self.chatHistory[-size:]

    def addChat(self, sender, senderIcon, text, ts):
        self.chatHistory.append({'sender' : sender,
                                 'senderIcon' : senderIcon,
                                 'type' : 'text',
                                 'data' : text,
                                 'timestamp' : ts})

    def addFile(self, sender, senderIcon, filename, data, ts):
        self.chatHistory.append({'sender' : sender,
                                 'senderIcon' : senderIcon,
                                 'type' : 'file',
                                 'data' : filename,
                                 'timestamp' : ts})
        self.files[filename] = data

    def getFile(self, filename):
        return None if filename not in self.files else self.files[filename]

class ChatroomManager():
    def __init__(self, rootDir):
        self.logger = createLogger('chatroom-agent')
        self.rootDir = rootDir
        self.indexFilename = os.path.join(self.rootDir, 'chatrooms.index.json')
        self.chatrooms = dict()

    def load(self):
        try:
            with open(self.indexFilename, 'r') as f:
                chatroomList = json.load(f)
        except FileNotFoundError:
            self.logger.warning('File not found')
            return False, "FileNotFoundError"
        else:
            self.logger.info('Successfully load chatroom index')
            for name in chatroomList:
                self.chatrooms[name] = Chatroom(name, os.path.join(self.rootDir, f'{name}.pkl'))
                self.chatrooms[name].load()
            return True

    def save(self):
        with open(self.indexFilename, 'w') as f:
            json.dump(list(self.chatrooms.keys()), f)
        for name in self.chatrooms:
            self.chatrooms[name].save()

    def createChatroom(self, name = '____', icon = '🦾', admins = [], members = []):
        if name in self.chatrooms:
            self.logger.info(f'createChatroom: chatroom \'{name}\' created failed (already exists)')
            return False, 'chatroom already exists'
        else:
            self.chatrooms[name] = Chatroom(name, os.path.join(self.rootDir, f'{name}.pkl'), icon, admins, members)
            self.chatrooms[name].save()
            self.logger.info(f'createChatroom: chatroom \'{name}\' created successfully')
        return True

    def showAllChatrooms(self):
        for name in self.chatrooms:
            print(self.chatrooms[name])

def test():
    crmgr = ChatroomManager('./chatrooms')
    crmgr.load()

    result = crmgr.createChatroom('blah', admins = ['wjpei'], members = ['wjpei'])
    crmgr.showAllChatrooms()

    crmgr.save()

if __name__ == '__main__':
    from misc import *
    test()

