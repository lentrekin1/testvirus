import socket, pickle, time

home = ('127.0.0.1', 5000)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect(home)

client.send(pickle.dumps('clientmsg'))

print(pickle.loads(client.recv(1024)))

time.sleep(5)
