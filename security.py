from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import os

def make_key():
    print('Generating private/public key pair...')
    keyPair = RSA.generate(3072)
    print('Generated new private/public key pair')
    return keyPair

def save_key(keys):
    with open('priv.pem', 'wb') as f:
        f.write(keys.exportKey())
    print('Saved private key to priv.pem')
    with open('pub.pem', 'wb') as f:
        f.write(keys.public_key().export_key())
    print('Saved public key to pub.pem')

def get_key():
    if not os.path.isfile('priv.pem') or not os.path.isfile('pub.pem'):
        print('Private and/or public key not found')
        keys = make_key()
        save_key(keys)
        return keys.exportKey(), keys.public_key().export_key()
    else:
        with open('priv.pem', 'r') as f:
            priv = RSA.import_key(f.read())
        print('Loaded private key')
        with open('pub.pem', 'r') as f:
            pub = RSA.import_key(f.read())
        print('Loaded public key')
        return priv, pub

def get_decryptor():
    key = get_key()[0]
    return PKCS1_OAEP.new(key)
