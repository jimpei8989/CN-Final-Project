import os, logging
import json, pickle
import hashlib, uuid, re
from backend.misc import createLogger 

def createSalt():
    return uuid.uuid4().hex

def hashPassword(password, salt):
    return hashlib.sha512((password + salt).encode('utf-8')).hexdigest()

class AccountAgent():
    def __init__(self, rootDir):
        self.logger = createLogger('account-agent')
        self.rootDir = rootDir
        self.indexFilename = os.path.join(self.rootDir, 'user.json')
        self.crFilename = os.path.join(self.rootDir, 'userChatrooms.pkl')
        self.database = dict()
        self.joinedChatrooms = dict()

    # Load & Save
    def load(self):
        try:
            with open(self.indexFilename, 'r') as f:
                self.database = json.load(f)
                assert type(self.database) is dict, "Error: Database should be a dictionary"
            with open(self.crFilename, 'rb') as f:
                self.joinedChatrooms = pickle.load(f)
                assert type(self.joinedChatrooms) is dict, "Error: Database should be a dictionary"
        except FileNotFoundError:
            self.logger.warning('File not found')
            return False, "FileNotFoundError"
        else:
            self.logger.info('Successfully load user information')
            return True

    def save(self):
        with open(self.indexFilename, 'w') as f:
            json.dump(self.database, f)
        with open(self.crFilename, 'wb') as f:
            pickle.dump(self.joinedChatrooms, f)

    def createUser(self, username, password):
        usernamePolicy = '^[0-9a-zA-Z_]{4,16}$'
        passwordPolicy = '^[0-9a-zA-Z_!@#\$%\^&]{8,32}$'
        if re.match(usernamePolicy, username) == None:
            self.logger.info(f'createUser : \'{username}\' username policy error')
            return False, f'Username format error (`{usernamePolicy}`)'
        elif username in self.database:
            self.logger.info(f'createUser : \'{username}\' already exists')
            return False, f'User \'{username}\' already exists!'
        elif re.match(passwordPolicy, password) == None:
            self.logger.info(f'createUser : \'{username}\' password policy error')
            return False, f'Password should match (`{passwordPolicy}`)'

        salt = createSalt()
        hashed = hashPassword(password, salt)
        self.database[username] = (salt, hashed)
        self.joinedChatrooms[username] = set()
        self.save()
        self.logger.info(f'createUser : \'{username}\' created successfully')
        return True

    def verifyUser(self, username, password):
        if username not in self.database:
            return False, f'User \'{username}\' not in database'
        salt, hashed = self.database[username]
        if hashPassword(password, salt) != hashed:
            return False, f'Incorrect username of password :('
        else:
            return True

    def addUsersToChatroom(self, users, name):
        for u in set(users):
            if u in self.joinedChatrooms:
                self.joinedChatrooms[u].add(name)
        self.save()

    def getChatroomList(self, user):
        return list(self.joinedChatrooms[user])


def test():
    a = AccountAgent('./.server/user-database.json')
    a.load()
    print(a.createUser('aaa', 'balhblah'))
    print(a.createUser('wjpei', 'tyuoi'))
    print(a.createUser('wjpei', 'qwertyuiop'))
    print(a.createUser('wjpei', 'adfs'))

    print(a.verifyUser('dylan', 'fghjdksa'))
    print(a.verifyUser('wjpei', 'asjfkd'))
    print(a.verifyUser('wjpei', 'qwertyuiop'))
    
if __name__ == '__main__':
    test()

