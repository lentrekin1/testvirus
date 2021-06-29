import subprocess

windowed = input('Windowed? (y/n) (default = n): ')
if windowed.lower().startswith('y'):
    print('Building windowed...')
    windowed = True
else:
    windowed = False
    print('Building windowless...')

if windowed:
    build_cmd = f'nuitka --standalone --onefile --windows-onefile-tempdir --python-arch=x86_64 --python-flag=no_site client.py'.split(' ')
else:
    build_cmd = f'nuitka --standalone --onefile --windows-onefile-tempdir --python-arch=x86_64 --python-flag=no_site --windows-disable-console client.py'.split(' ')

proc = subprocess.Popen(build_cmd, shell=True)
proc.communicate()