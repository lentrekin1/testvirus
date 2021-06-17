#todo use https://antiscan.me


import socket, pickle, time
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

home = ('127.0.0.1', 5000)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
encryptor = PKCS1_OAEP.new(RSA.import_key(open('pub.pem').read()))
#todo decide how to give pub key to client.py

def send(msg):
    msg = encryptor.encrypt(pickle.dumps(msg))
    client.send(msg)

def run():
    client.connect(home)
    print(f'client connected to {home[0]}:{home[1]}')

    send('msg from client')

    print(f'msg recv from {home[0]}:{home[1]}: {pickle.loads(client.recv(1024))}')

    time.sleep(20)
    print('client closed')
    return

if __name__ == '__main__':
    run()
