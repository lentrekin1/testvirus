#use https://antiscan.me
import datetime
import socket, pickle, time, platform, psutil
import traceback
#from Crypto.PublicKey import RSA
#from Crypto.Cipher import PKCS1_OAEP

home = ('192.168.0.224', 5000)
conn = None
#encryptor = PKCS1_OAEP.new(RSA.import_key(open('pub.pem').read()))
conn_open = False
#todo decide how to give pub key to client.py - maybe  --include-plugin-files=PATTERN or --include-data-file=DATA_FILES in build cmd

def get_size(b, s="B"):
    f = 1024
    for u in ["", "K", "M", "G", "T", "P"]:
        if b < f:
            return f"{b:.2f}{u}{s}"
        b /= f

def send(msg):
    #msg = encryptor.encrypt(pickle.dumps(msg))
    conn.send(pickle.dumps(msg))

def run():
    global conn_open, conn
    while True:
        if not conn:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            conn.connect(home)
            print(f'Client connected to {home[0]}:{home[1]}')
            send({'name': socket.gethostname()})
            print(f'Sent {socket.gethostname()} to home as nickname')
            server_alive = True
        except:
            traceback.print_exc()
            print('Could not connect to server')
            server_alive = False
            time.sleep(5)

        while server_alive:
            try:
                cmd = pickle.loads(conn.recv(1024))
                if cmd != 'keepalive':
                    print(f'Command recieved from {home[0]}:{home[1]}: {cmd}')

                if cmd == 'getinfo':
                    response = {}
                    response['platform'] = platform.platform()
                    response['processor'] = platform.processor()
                    response['boot time'] = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime('%m-%d-%Y %I:%M:%S%p')
                    response['core counts'] = f'physical: {psutil.cpu_count(logical=False)}, total: {psutil.cpu_count(logical=True)}'
                    response['memory'] = f'total: {get_size(psutil.virtual_memory().total)}, available: {get_size(psutil.virtual_memory().available)}'
                    for p in psutil.disk_partitions():
                        try:
                            response[p.device] = f'disk size: {get_size(psutil.disk_usage(p.mountpoint).total)}, used: {get_size(psutil.disk_usage(p.mountpoint).used)}'
                        except:
                            response[p.device] = f'disk size: disk not ready, used: disk not ready'
                        response[p.device] += f', mountpoint: {p.mountpoint}, file system type: {p.fstype}'
                    response['battery'] = psutil.sensors_battery()
                    #response['']
                    send(response)
            except:
                server_alive = False
                conn = None
                print('Invalid msg from server, assuming server down')

if __name__ == '__main__':
    run()
