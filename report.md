# 2019 Computer Network Final Project - cnMessage Report

### Team Members
- **Team 2 (柯宏穎請大家吃飯)**
- B06902029 裴梧鈞
- B06902049 林首志
- B06902097 楊皓丞

### 1. User & Operation Guide
#### Prerequisites
Our server and client were written in Python 3.7. The following Python package is required:

- `emoji`

Also, [chafa](https://hpjansson.org/chafa/download/) was used to implement a great feature in our project. Please install it on your platform.

#### Register / Login
TODO: ADD IMAGE

Input your username and password (passwords will not be echoed). If the username is not present in the server database, we'll register one account for you.

Also, we have regex restriction on username and password.
- username: `^[0-9a-zA-Z_]{4,16}$`<br>usernames should be composed of numbers, uppercase / lowercase English alphabets, or underscores. The length should be between 4 and 16 characters.
- password: `^[0-9a-zA-Z_!@#\$%\^&]{8,32}$`<br>passwords should be composed of numbers, uppercase / lowercase English alphabets, or these special characters: `_!@#$%^&`. The length should be between 8 and 32 characters.

#### Usage Guide

TODO: Add image

There are three modes, `ctrl`, `help` and `text`.
- In `ctrl` mode:
    -  press `:` and then enter a command:
        - `help`: print this message
        - `create CHATROOM_NAME CHATROOM_ICON CHATROOM_MEMBERS`: create a chatroom, you should separate each member with a single comma without spaces
        - `enter CHATROOM_NAME/CHATROOM_NUM`: go into a chatroom
        - `upload FILENAME`: upload a file to the chatroom
            **YOU MUST BE IN A CHATROOM TO PERFORM THIS**
        - `download FILENAME [DOWNLOAD_PATH]`: download a file from the chatroom to the download path (default: `~/Downloads`)
            **YOU MUST BE IN A CHATROOM TO PERFORM THIS**
        - `image FILENAME`: send an image that can be shown in the command line interface using chafa
        - `exit`: exit the chatroom
    - Or enter any printable ascii character to enter `text` mode
        **YOU MUST BE IN A CHATROOM TO PERFORM THIS**
- In `help` mode:
    - press `q` to exit
- In `text` mode:
    - form your message with any printable characters
    - press `<ENTER>` to send the message
    - press `<ESC>` to enter `ctrl` mode


### 2. Instruction on How to Run Server & Clients
#### Server
```bash
python3 src/server.py [-p PORT]
```
- `-p PORT`: specify server port (default: `1126`)

#### Client
```bash
python3 src/client-ui.py [-s SERVER_ADDR] [-p PORT]
```
- `-s SERVER_ADDR`: specify server address (default: `localhost`)
- `-p PORT`: specify server port (default: `1126`)

### 3. System & Program Design

#### Server
Our server plays the role of data exchange and storage center.
The main functions of our server were implemented by the following components:
1. AccountAgent
    - Handle register & login<br>Remember usernames, password salts and password hashes.
    - Keep user information<br>Such as users' chatrooms, users' icons.
2. ChatroomManager
    - Keep all information of each chatroom, such as the users, admins, chatroom icon, chat history, transmitted files...


#### Client
- Uses Python built-in [curses](https://docs.python.org/3/library/curses.html) module to build user interface.
- Request the lastest "chatroom list" and "chat history" on every key stroke.
- Display the information above on the screen.
- Send corresponding request after inputting commands in `ctrl` mode.

#### Data Transmit
Unlike those who use php, we spend a lot of time dealing with TCP sockets.
- Socket I/O
    - Server: blocking with select
    - Client: common client socket design (using `connect()`)
- We use JSON as the medium of data exchange.
- In file transfer, the transmitting bytes are encoded in base64.

#### Chat History
Chat history is displayed in the following three categories.
1. `text` <br>Normal text.
2. `file`<br>Only filename is transmitted and displayed. File content are only transmitted when you request to do it.
3. `image`<br>As mentioned in the first section, we use [chafa](https://hpjansson.org/chafa/download/) to show images on terminal. We take three key attributes, characters, foreground colors and background colors of each character, from the output of chafa, compress them and send them to the server. Afterwards the clients display the image according to those attributes.

### 4. Other things you want to say, if any.