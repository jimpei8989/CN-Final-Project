import os
import json, pickle
import uuid
from backend.misc import createLogger

class Chatroom():
    def __init__(self, ID, filename, name, icon, admins = set(), members = set()):
        self.ID = ID
        self.filename = filename
        self.displayName = name
        self.icon = icon

        # Load
        self.admins = admins if type(admins) is set else set(admins)
        self.members = members if type(members) is set else set(members)
        self.chatHistory = []

    def __str__(self):
        return f'''
====== {self.ID} ======
displayName: {self.displayName}
Admins: {self.admins}
Members: {self.members}
chatHistory: {self.chatHistory}
'''[1:-1]

    def save(self):
        with open(self.filename, 'wb') as f:
            pickle.dump((self.displayName, self.admins, self.members, self.chatHistory), f)


    def load(self):
        with open(self.filename, 'rb') as f:
            self.displayName, self.admins, self.members, self.chatHistory = pickle.load(f)

    def getID(self):
        return self.ID

    def isMember(self, user):
        return user in self.members or user in self.admins

    def isAdmin(self, user):
        return user in self.admins

    def getChatHistory(self, size):
        size = min(size, len(self.chatHistory))
        return self.chatHistory[-size:]

    def appendChat(self, chat):
        self.chatHistory.append(chat)

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
            for ID in chatroomList:
                self.chatrooms[ID] = Chatroom(ID, os.path.join(self.rootDir, f'{ID}.pkl'))
                self.chatrooms[ID].load()
            return True

    def save(self):
        with open(self.indexFilename, 'w') as f:
            json.dump(list(self.chatrooms.keys()), f)
        for ID in self.chatrooms:
            self.chatrooms[ID].save()

    def createChatroom(self, user, name = '____', icon = '🦾', admins = [], members = []):
        ID = uuid.uuid4().hex
        self.chatrooms[ID] = Chatroom(ID, os.path.join(self.rootDir, f'{ID}.pkl'), name, icon, admins, members)
        self.chatrooms[ID].save()
        self.logger.info(f'createChatroom: \'{user}\' create chatroom \'{name}\' successfully')
        return True, ID

    def showAllChatrooms(self, ID):
        if ID in self.chatrooms:
            print(self.chatrooms[ID])
            self.logger.info(f'showChatroom: {ID}')
        else:
            self.logger.info(f'showChatroom: {ID} does not exist')

def test():
    crmgr = ChatroomManager('./chatrooms')
    crmgr.load()

    result, ID = crmgr.createChatroom('wjpei', 'blah', ['wjpei'], ['wjpei'])
    crmgr.showAllChatrooms(ID)

    crmgr.save()

if __name__ == '__main__':
    from misc import *
    test()

