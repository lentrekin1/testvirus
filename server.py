import socket, pickle

addr = ('127.0.0.1', 5000)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(addr)
server.listen()

conn = server.accept()

print(pickle.loads(conn[0].recv(1024)))

conn[0].send(pickle.dumps('servermsg'))
