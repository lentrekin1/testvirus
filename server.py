import socket, pickle, security
import threading, traceback

addr = ('127.0.0.1', 5000)
decryptor = security.get_decryptor()
#todo - client->server communication encrypted, server->client not

users = []

def is_int(str):
    try:
        return int(str)
    except:
        return False

class User():
    def __init__(self, conn):
        self.conn = conn
        self.ip, self.port = conn[1][0], conn[1][1]
        self.hist = []
        self.msg = None

    def send(self, msg):
        self.conn[0].send(pickle.dumps(msg))
        self.hist.append({'from': 'server', 'msg': msg})

    def read(self):
        try:
            self.msg = self.conn[0].recv(4096)
            self.msg = clean(self.msg)
        except ConnectionAbortedError: #todo this might not work when not on 127.0.0.1
            self.hist.append({'from': 'server', 'msg': 'client disconnected'})
            return -2
        if self.msg != -1:
            self.hist.append({'from': 'client', 'msg': self.msg})
            return self.msg

def clean(msg):
    try:
        msg = decryptor.decrypt(msg)
        return pickle.loads(msg)
    except ValueError:
        return -1

def handle_user(user):
    while True:
        msg = user.read()
        if msg:
            if msg == -2:
                #todo maybe dont stop monitoring on dc?
                #print(f'{user.ip}:{user.port} disconnected')
                return
            else:
                #print(f'msg recv from user at {user.ip}:{user.port}: {msg}')
                user.send('msg from server')
        else:
            #todo make this better
            #print(f'invalid msg recv from {user.ip}:{user.port}, notifying client')
            user.send('invalid input recv')

def get_instructions():
    instruction = None
    while instruction not in [1, 2]:
        print('''
Options:
1. View running bots
2. Remove inactive bots''')
        instruction = is_int(input('Chose a number: '))
        if instruction not in [1, 2]:
            print('Invalid option')
    if instruction == 1:
        instruction = None
        while instruction not in [x for x in range(0, len(users) + 1)]:
            msg = 'Running bots:\n'
            for user in enumerate(users):
                msg += f'{user[0] + 1}. {user[1].ip}:{user[1].port}\n'
            msg += '0. Back'
            print(msg)
            instruction = is_int(input('Chose a number: '))
            if instruction not in [x for x in range(0, len(users) + 1)]:
                print('Invalid option')
        #todo menu logic - https://console-menu.readthedocs.io/en/latest/
    else:
        pass


def run():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(addr)
    server.listen()
    print(f'server running on {addr[0]}:{addr[1]}')

    threading.Thread(target=get_instructions, args=()).start()

    while True:
        conn = server.accept()
        user = User(conn)
        users.append(user)
        #print(f'connection recv from {user.ip}:{user.port}')
        threading.Thread(target=handle_user, args=(user, )).start()


if __name__ == '__main__':
    run()