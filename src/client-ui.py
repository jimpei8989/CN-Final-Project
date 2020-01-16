import os, sys, time, logging, signal
import base64
import string
from constants import *

# UI
import curses

# Exchange
import json
import socket, ssl
from getpass import getpass

def getInput(screen, r, c, promptString, echo = True, length = 1000):
    if echo: curses.echo()
    else: curses.noecho()
    curses.curs_set(1)
    screen.addstr(r, c, promptString)
    screen.refresh()
    ipt = screen.getstr(r, c + len(promptString), length)
    curses.noecho()
    curses.curs_set(0)
    return ipt.decode('utf-8')

class Client():
    def __init__(self, screen, activeWindows):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.screen = screen
        self.username = None
        self.activeWindows = activeWindows

    def connect(self, hostname = 'localhost', port = 2900):
        self.sock.connect((hostname, port))

    def send(self, message):
        self.sock.send(message.encode('utf-8'))

    def recv(self):
        return self.sock.recv(MAX_BUFFER_SIZE).decode('UTF-8')

    def login(self, relogin = 3):
        screen = self.screen
        nRows, nCols = screen.getmaxyx()
        loginWindow = curses.newwin(nRows, nCols, 0, 0)

        self.activeWindows[loginWindow] = None
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

        username = getInput(loginWindow, usernameBeginRow, usernameBeginCol, "Username: ", length = 16)
        password = getInput(loginWindow, passwordBeginRow, usernameBeginCol, "Password: ", echo = False, length = 20)

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
                del self.activeWindows[loginWindow]
                del loginWindow
                self.login(relogin = 3 if relogin is False else relogin - 1)
        else:
            self.username = username
            loginSuccessMessage = ('Register + ' if resultRegistration else '') + 'Login success! Press any key to continue...'
            loginWindow.addstr(usernameBeginRow + 3, 1, ' ' * (nCols - 2))
            loginWindow.addstr(usernameBeginRow + 3, (nCols - len(loginSuccessMessage)) // 2, loginSuccessMessage)
            loginWindow.getkey()
            del self.activeWindows[loginWindow]
            del loginWindow
    
    def createChatroom(self):
        name = input('Chatroom Name: ')
        people = input('Talking With: ').split(', ')[0]
        data = {'type' : 'CreateChatroom', 'name' : name, 'admins' : [self.username, people], 'members' : [self.username, people]}
        self.send(json.dumps(data))
        msg = self.recv()
        ID = msg.split('|')[1]
        return ID

    def chat(self, ID):
        text = input(f'{self.username}> ')
        data = {'type' : 'Messaging', 'ID' : ID, 'text' : text}
        self.send(json.dumps(data))
        msg = self.recv()

    def start(self):
        # Get screen size and define pad size
        nRows, nCols = self.screen.getmaxyx()
        verticalCut = int(0.3 * nCols)
        horizontalCut = int(0.85 * nRows)

        # create main window
        mainWindow = curses.newwin(nRows, nCols, 0, 0)
        self.activeWindows[mainWindow] = None

        def displayFramework():
            mainWindow.box()
            mainWindow.addch(0, verticalCut, curses.ACS_TTEE)
            mainWindow.vline(1, verticalCut, curses.ACS_VLINE, nRows - 2)
            mainWindow.addch(nRows - 1, verticalCut, curses.ACS_BTEE)
            mainWindow.addch(horizontalCut, verticalCut, curses.ACS_LTEE)
            mainWindow.hline(horizontalCut, verticalCut + 1, curses.ACS_HLINE, nCols - verticalCut - 2)
            mainWindow.addch(horizontalCut, nCols - 1, curses.ACS_RTEE)

        displayFramework()
        mainWindow.refresh()

        # create left pad
        leftPad = curses.newpad(1000, nCols)
        self.activeWindows[leftPad] = (0, 0, 1, 1, nRows - 2, verticalCut - 1)
        leftPadWidth = verticalCut - 1  # [1, verticalCut - 1] (0-based)
        leftPadHeight = nRows - 2       # [1, nRows - 2] (0-based)

        def getChatroomList():
            data = {'type' : 'GetChatroomList'}
            self.send(json.dumps(data))
            msg = self.recv()
            self.chatroomList = set(map(tuple, sorted(json.loads(msg.split('|')[1]))))
            return self.chatroomList

        def displayChatroomList(chatroomList):
            # chatroomList is a list of 3-tuple of strings (name, icon, last ts)
            rowCount = 0
            for i, c in enumerate(chatroomList):
                if i != 0:
                    leftPad.addstr(rowCount, 0, '-' * leftPadWidth)
                    rowCount += 1
                leftPad.addstr(rowCount, 0, f'[{i:2d}] {c[1]} - {c[0]}')
                leftPad.addstr(rowCount + 1, 0, f'{c[0]}')
                rowCount += 2
            leftPad.refresh(0, 0, 1, 1, nRows - 2, verticalCut - 1)

        #  displayChatroomList([("d4f37de8202944c89fe4aadcb9e27882", "HAHA", "😀"), ("8a4f6e74134b4cce96f8aa611d0b8f22", "love", "💕"), ("c7326620491b4231be408ca4e26fe871", "final exam", "😢")] * 3)

        # create chat pad
        chatPad = curses.newpad(1000, nCols)
        self.activeWindows[chatPad] = (0, 0, 1, verticalCut + 1, horizontalCut - 1, nCols - 1)
        chatPadWidth = nCols - verticalCut - 1
        chatPadHeight = horizontalCut - 1
        widthPerLine = int(chatPadWidth * 0.5)

        def getChats(name):
            data = {'type' : 'GetChatHistory', 'name' : name}
            self.send(json.dumps(data))
            msg = self.recv()
            chats = json.loads(msg.split('|')[1])
            return chats

        def displayChat(chats):
            # chats is a list of (sender, senderIcon, type, data, time)
            chatPad.erase()
            rowCount = 0
            def alignLeft(header, lines):
                nonlocal rowCount
                chatPad.addstr(rowCount, 0, header)
                rowCount += 1
                for line in lines:
                    chatPad.addstr(rowCount, 0, line)
                    rowCount += 1
                rowCount += 1
            def alignRight(header, lines):
                nonlocal rowCount
                chatPad.addstr(rowCount, chatPadWidth - len(header) - 2, header)
                rowCount += 1
                for line in lines:
                    chatPad.addstr(rowCount, chatPadWidth - len(line) - 2, line)
                    rowCount += 1
                rowCount += 1
            for chat in chats:
                sender, icon, typee, data, time = chat
                displayHeader = f'{icon} [{sender}] at {time}'
                if sender == self.username:
                    if typee == 'text':
                        displayText = [data[i : i + widthPerLine] + ' <<<' for i in range(0, len(data), widthPerLine)]
                    elif typee == 'file':
                        displayText = [f'FILE : "{data}" <~~']
                    alignRight(displayHeader, displayText)
                else:
                    if typee == 'text':
                        displayText = ['>>> ' + data[i : i + widthPerLine] for i in range(0, len(data), widthPerLine)]
                    elif typee == 'file':
                        displayText = [f'~~> FILE : "{data}"']
                    alignLeft(displayHeader, displayText)
            chatPad.refresh(0 if rowCount < chatPadHeight else rowCount - chatPadHeight, 0, 1, verticalCut + 1, horizontalCut - 1, nCols - 2)

        def displayPusheen():
            pusheen = '''
Type :help to get more instructions



     ▐▀▄       ▄▀▌   ▄▄▄▄▄▄▄             
    ▌▒▒▀▄▄▄▄▄▀▒▒▐▄▀▀▒██▒██▒▀▀▄          
   ▐▒▒▒▒▀▒▀▒▀▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▀▄        
   ▌▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▄▒▒▒▒▒▒▒▒▒▒▒▒▀▄      
 ▀█▒▒▒█▌▒▒█▒▒▐█▒▒▒▀▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▌     
 ▀▌▒▒▒▒▒▒▀▒▀▒▒▒▒▒▒▀▀▒▒▒▒▒▒▒▒▒▒▒▒▒▒▐   ▄▄
 ▐▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▌▄█▒█
 ▐▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒█▒█▀ 
 ▐▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒█▀   
 ▐▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▌    
  ▌▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▐     
  ▐▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▌     
   ▌▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▐      
   ▐▄▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▄▌      
     ▀▄▄▀▀▀▀▀▄▄▀▀▀▀▀▀▀▄▄▀▀▀▀▀▄▄▀  
'''[1:-1].split('\n')
            width = max(len(l) for l in pusheen)
            height = len(pusheen)

            chatPad.erase()
            for i, line in enumerate(pusheen):
                chatPad.addstr(horizontalCut - height  - 2 + i, (chatPadWidth - width) // 2, line) 
            chatPad.refresh(0, 0, 1, verticalCut + 1, horizontalCut - 1, nCols - 2)

        def displayHelpMessage():
            message = '''
There are three modes, `ctrl`, `help` and `text` modes.
In `ctrl` mode:
    > you first press a ':' and then enter a command:
        - help
            enter this page

        - create CHATROOM_NAME CHATROOM_ICON CHATROOM_MEMBERS
            create a chatroom
            you should seperate each member with a single comma without spaces

        - enter CHATROOM_NAME
            go into a chatroom

        - upload FILENAME
            upload a file to the chatroom
            **YOU MUST NEED TO BE IN A CHATROOM TO PERFORM THIS**

        - download FILENAME
            download a file from the chatroom
            **YOU MUST NEED TO BE IN A CHATROOM TO PERFORM THIS**

        - exit
            exit the chatroom

    > Or enter any printable ascii to go into `text` mode
        **YOU MUST NEED TO BE IN A CHATROOM TO PERFORM THIS**
        
In `help` mode:
    - Press `q` to exit

In `text` mode:
    - type ascii printable characters to type
    - press `enter` to send message
    - press `esc` to go into `ctrl` mode
'''[1:-1].split('\n')
            height = len(message)

            chatPad.erase()
            for i, line in enumerate(message):
                chatPad.addstr(i, 0, line) 
            chatPad.refresh(0, 0, 1, verticalCut + 1, horizontalCut - 1, nCols - 2)

        #  displayChat([(f'{self.username}', '🙃', 'text', 'Hi!', '2020/01/12 00:01:50'), ('dylan', '🤠', 'text', 'Hello', '2020/01/12 00:01:59'), ('howard', '😖', 'text', 'Ni nei nei deeee', '2020/01/12 00:02:13'), ('devin', '👽', 'text', 'wwwwwwwwwwwwwwwwwwwwwww', '2020/01/12 00:03:20'), (f'{self.username}', '🙃', 'text', 'a' * 200, '2020/01/12 00:01:50'), ('dylan', '🤠', 'text', 'b' * 100, '2020/01/12 00:01:59'), ('howard', '😖', 'text', 'c' * 150, '2020/01/12 00:02:13'), ('devin', '👽', 'text', 'd' * 20, '2020/01/12 00:03:20'), (f'{self.username}', '🙃', 'file', 'file.txt', '2020/01/12 00:05:50'), ('dylan', '🤠', 'file', 'pornhub.mov', '2020/01/12 00:11:03')] * 3)

        textWidth = nCols - verticalCut - 2
        textHeight = nRows - horizontalCut - 2
        currentChatroom = None
        mode = 'ctrl'
        mainWindow.addstr(horizontalCut, verticalCut + 3, f'({mode:4s})')
        buf = ''
        while True:
            # Display left pad
            self.chatroomList = getChatroomList()
            displayChatroomList(self.chatroomList)

            # Display chat pad
            if mode == 'help':
                displayHelpMessage()
            else:
                if currentChatroom is not None:
                    chats = getChats(currentChatroom)
                    displayChat(chats)
                else:
                    displayPusheen()


            key = mainWindow.getkey()
            # Get input
            if mode == 'ctrl':
                if key == ':':
                    commands = getInput(mainWindow, horizontalCut + 1, verticalCut + 1, ':', True, length = textWidth).split(' ')
                    mainWindow.addstr(horizontalCut + 1, verticalCut + 1, ' ' * textWidth)

                    command = commands[0]
                    if command == 'help' or command == 'h':
                        mode = 'help'

                    elif command == 'create' or command == 'c':
                        name = commands[1]
                        icon = commands[2]
                        mates = commands[3].split(',')
                        data = {'type' : 'CreateChatroom',
                                'name' : name,
                                'icon' : icon,
                                'admins' : [self.username] + mates,
                                'members' : [self.username] + mates}
                        self.send(json.dumps(data))
                        msg = self.recv()
                        verdit = msg.split('|')

                    #TODO
                    elif command == 'enter' or command == 'e':
                        name = commands[1]
                        if name in [c[0] for c in self.chatroomList]:
                            currentChatroom = name

                    #TODO
                    elif command == 'upload':
                        if currentChatroom is not None:
                            filename = commands[1]
                            with open(filename, 'rb') as f:
                                content = base64.b64encode(f.read())
                            head, tail = os.path.split(filename)
                            data = {'type' : 'UploadFile',
                                    'name' : currentChatroom,
                                    'filename' : tail,
                                    'content' : content}
                            self.send(json.dumps(data))
                            msg = self.recv()

                    #TODO
                    elif command == 'download':
                        if currentChatroom is not None:
                            filename = commands[1]
                            data = {'type' : 'UploadFile',
                                    'name' : currentChatroom,
                                    'filename' : filename}
                            self.send(json.dumps(data))
                            msg = self.recv()
                            verdit = msg.split('|')[0]
                            if verdit == 'OK':
                                content = msg.split('|')[1]
                                with open(os.path.join('~', 'Downloads', filename), 'wb') as f:
                                    f.write(base64.b64decode(f.read()))

                    elif command == 'updateIcon':
                        icon = commands[1]
                        data = {'type' : 'UpdateIcon',
                                'icon' : icon}
                        self.send(json.dumps(data))
                        msg = self.recv()
                        verdit = msg.split('|')[0]

                    elif command == 'exit' or command == 'q':
                        currentChatroom = None

                elif key in string.printable:
                    if currentChatroom is not None:
                        mode = 'text'
                        mainWindow.addstr(horizontalCut, verticalCut + 3, f'({mode:4s})')
                        buf = key

            elif mode == 'help':
                if key == 'q':
                    mode = 'ctrl'
            elif mode == 'text':
                if key == chr(27):   # esc
                    buf = ''
                    mode = 'ctrl'
                    mainWindow.addstr(horizontalCut, verticalCut + 3, f'({mode:4s})')
                elif key == chr(10): #enter
                    if buf != '':
                        data = {'type' : 'Messaging',
                                'name' : currentChatroom,
                                'text' : buf}
                        self.send(json.dumps(data))
                        msg = self.recv()
                        verdit = msg.split('|')
                        buf = ''
                elif key == chr(127):  # Backspace
                    buf = buf[:-1] if len(buf) > 0 else buf
                elif key in string.printable:
                    buf = buf + key

            for i in range(textHeight):
                mainWindow.addstr(horizontalCut + 1 + i, verticalCut + 1, ' ' * textWidth)

            tmpbuf = buf + '_'
            lines = [tmpbuf[i : i + textWidth] for i in range(0, len(tmpbuf), textWidth)]
            for i, l in enumerate(lines[-textHeight:]):
                mainWindow.addstr(horizontalCut + 1 + i, verticalCut + 1, l)

            mainWindow.refresh()
            time.sleep(0.01)


def main(screen):
    activeWindows = dict()
    def handler(signum, frame):
        nRows, nCols = screen.getmaxyx()
        height, width = 10, 32
        quitWindow = curses.newwin(height, width, (nRows - height) // 2, (nCols - width) // 2)
        quitWindow.box()

        quitMessages = ['Press <q> to quit', 'Press <ESC> to continue']
        for i, m in enumerate(quitMessages):
            quitWindow.addstr((height - len(quitMessages)) // 2 + i, (width - len(m)) // 2, m)
        quitWindow.refresh()

        curses.noecho()
        while True:
            key = quitWindow.getkey()
            if key == 'q':
                exit(0)
            elif key == '\x1b':
                for win in activeWindows:
                    if activeWindows[win] is None:  # is a window
                        win.redrawwin()
                        win.refresh()
                    else:                           # is a pad
                        win.refresh(*activeWindows[win])

    # Handle signal
    signal.signal(signal.SIGINT, handler)

    # Set self.logger config
    logging.basicConfig(filename = 'client.log',
                        filemode = 'w',
                        )

    # curses settings
    curses.noecho()
    curses.curs_set(0)

    client = Client(screen, activeWindows)
    client.connect()

    # Register / Login
    client.login(False)

    # Start
    client.start()

if __name__ == '__main__':
    curses.wrapper(main)

