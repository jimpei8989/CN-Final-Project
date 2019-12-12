import os
import json
import hashlib, uuid, re

def createSalt():
    return uuid.uuid4().hex

def hashPassword(password, salt):
    return hashlib.sha512((password + salt).encode('utf-8')).hexdigest()

class AccountAgent():
    def __init__(self, filename):
        self.database = dict()
        self.saveto = filename

    def load(self):
        try:
            with open(self.saveto, 'r') as f:
                self.database = json.load(f)
                assert type(self.database) is dict, "Error: Database should be a dictionary"
        except FileNotFoundError:
            return False, "FileNotFoundError"
        else:
            return True

    def save(self):
        with open(self.saveto, 'w') as f:
            json.dump(self.database, f)

    def createUser(self, username, password):
        usernamePolicy = '^[0-9a-zA-Z_]{4,16}$'
        passwordPolicy = '^[0-9a-zA-Z_!@#\$%\^&]{8,32}$'
        if re.match(usernamePolicy, username) == None:
            return None, f'Username Format Error ({usernamePolicy})'
        elif username in self.database:
            return None, f'User \'{username}\' already existed!'
        elif re.match(passwordPolicy, password) == None:
            return None, f'Password should match ({passwordPolicy})'

        salt = createSalt()
        hashed = hashPassword(password, salt)
        self.database[username] = (salt, hashed)
        self.save()

    # TODO: change the error message to 'Incorrect username or password :('
    def verifyUser(self, username, password):
        if username not in self.database:
            return None, f'User \'{username}\' not in database'
        salt, hashed = self.database[username]
        if hashPassword(password, salt) != hashed:
            return None, f'Wrong password'
        else:
            return True

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
    
test()
