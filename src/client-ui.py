import os, sys, time, logging, signal
from constants import *

# UI
import curses
from pynput import keyboard

# Exchange
import json
import socket, ssl
from getpass import getpass

class Client():
    def __init__(self, screen):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.screen = screen
        self.username = None

    def connect(self, hostname = 'localhost', port = 2900):
        self.sock.connect((hostname, port))

    def send(self, message):
        self.sock.send(message.encode('utf-8'))

    def recv(self):
        return self.sock.recv(MAX_BUFFER_SIZE).decode('UTF-8')

    def login(self, relogin = 3):
        def getInput(screen, r, c, promptString, echo = True):
            if echo: curses.echo()
            else: curses.noecho()
            screen.addstr(r, c, promptString)
            screen.refresh()
            ipt = screen.getstr(r, c + len(promptString), 20)
            curses.noecho()
            return ipt

        screen = self.screen
        nRows, nCols = screen.getmaxyx()
        loginWindow = curses.newwin(nRows, nCols, 0, 0)
        loginWindow.box()

        # Show "I-Ru" Banner"
        banner = '''
ooooo        ooooooooo.                     .             oooo  oooo
`888'        `888   `Y88.                 .o8             `888  `888
 888          888   .d88' oooo  oooo    .o888oo  .oooo.    888   888  oooo
 888          888ooo88P'  `888  `888      888   `P  )88b   888   888 .8P'
 888  888888  888`88b.     888   888      888    .oP"888   888   888888.
 888          888  `88b.   888   888      888 . d8(  888   888   888 `88b.
o888o        o888o  o888o  `V88V"V8P'     "888" `Y888""8o o888o o888o o888o
'''.split('\n')[1:-1]

        bannerHeight = len(banner)
        bannerWidth = max(len(l) for l in banner)
        bannerBeginRow = max(3, nRows // 5)
        bannerBeginCol = max(3, (nCols - bannerWidth) // 2)
        curses.init_pair(1, 197, 0)

        for i, l in enumerate(banner):
            loginWindow.addstr(bannerBeginRow + i, bannerBeginCol, l, curses.color_pair(1))
        #  loginWindow.refresh()

        # Get username and password
        usernameBeginRow = min(nRows - 6, int(0.7 * nRows))
        usernameBeginCol = max(int(0.3 * nCols), nCols // 2 - 15)
        passwordBeginRow = usernameBeginRow + 1
        passwordBeginCol = usernameBeginCol

        characterPerLine = int(0.4 * nCols)

        if relogin != False:
            reloginMessage = f' Incorrect username or password! ({relogin})'
            curses.init_pair(2, 160, 227)
            loginWindow.addstr(usernameBeginRow + 3, usernameBeginCol - 1, reloginMessage, curses.color_pair(2) | curses.A_BLINK)
        else:
            registerMessage = 'We\'ll register for you if you haven\'t registered yet'
            if len(registerMessage) > characterPerLine:
                loginWindow.addstr(usernameBeginRow + 3, usernameBeginCol, registerMessage[:characterPerLine], curses.A_BLINK)
                loginWindow.addstr(usernameBeginRow + 4, usernameBeginCol, registerMessage[characterPerLine:], curses.A_BLINK)
            else:
                loginWindow.addstr(usernameBeginRow + 3, (nCols - len(registerMessage)) // 2, registerMessage, curses.A_BLINK)


        username = getInput(loginWindow, usernameBeginRow, usernameBeginCol, "Username: ").decode('utf-8')
        password = getInput(loginWindow, passwordBeginRow, usernameBeginCol, "Password: ", echo = False).decode('utf-8')

        # Send packet and check result
        data = {'type' : 'Register', 'username' : username, 'password' : password}
        self.send(json.dumps(data))
        msg = self.recv()
        resultRegistration = True if 'OK' in msg else False

        data = {'type' : 'Login', 'username' : username, 'password' : password}
        self.send(json.dumps(data))
        msg = self.recv()
        resultLogin = True if 'OK' in msg else False

        if resultLogin is False:
            if relogin == 1:
                exit(0)
            else:
                self.login(relogin = 3 if relogin is False else relogin - 1)
                del loginWindow
        else:
            loginSuccessMessage = ('Register + ' if resultRegistration else '') + 'Login success! Press any key to continue...'
            loginWindow.addstr(usernameBeginRow + 3, 1, ' ' * (nCols - 2))
            loginWindow.addstr(usernameBeginRow + 3, (nCols - len(loginSuccessMessage)) // 2, loginSuccessMessage)
            loginWindow.getkey()
            exit(0)


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

    def start(self):
        pass




def main(screen):
    # Referene: https://pythonhosted.org/pynput/keyboard.html
    class ReleaseKeyException(Exception): pass

    def on_release(key):
        pressedKey = key
        if key == keyboard.KeyCode(char = 'q') or key == keyboard.Key.esc:
            raise ReleaseKeyException(key)

    def handler(signum, frame):
        nRows, nCols = screen.getmaxyx()
        height, width = 10, 32
        quitWindow = curses.newwin(height, width, (nRows - height) // 2, (nCols - width) // 2)
        quitWindow.box()

        quitMessages = ['Press <q> to quit', 'Press <ESC> to continue']
        for i, m in enumerate(quitMessages):
            quitWindow.addstr((height - len(quitMessages)) // 2 + i, (width - len(m)) // 2, m)
        quitWindow.refresh()

        with keyboard.Listener(on_release = on_release) as listener:
            try:
                listener.join()
            except ReleaseKeyException as e:
                pressedKey = e.args[0]
                if pressedKey == keyboard.KeyCode(char = 'q'):
                    # Start destroy self
                    exit(0)
                else:
                    del quitWindow
                    # TODO: restore windows
                    screen.refresh()

    # Handle signal
    signal.signal(signal.SIGINT, handler)

    # Set self.logger config
    logging.basicConfig(filename = 'client.log',
                        filemode = 'w',
                        )

    client = Client(screen)
    client.connect()

    client.login(False)
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
    curses.wrapper(main)

