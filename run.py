import time, client, server, threading

s = threading.Thread(target=server.run, args=())
c = threading.Thread(target=client.run, args=())
s.start()
time.sleep(1)
c.start()
