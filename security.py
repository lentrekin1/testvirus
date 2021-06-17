from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import binascii, pickle, os

def make_key():
    print('generating private/public key pair...')
    keyPair = RSA.generate(3072)
    print('generated new private/public key pair')
    return keyPair
    '''pubKey = keyPair.publickey()
    print(f"Public key:  (n={hex(pubKey.n)}, e={hex(pubKey.e)})")
    pubKeyPEM = pubKey.exportKey()
    print(pubKeyPEM.decode('ascii'))
    
    print(f"Private key: (n={hex(pubKey.n)}, d={hex(keyPair.d)})")
    privKeyPEM = keyPair.exportKey()
    print(privKeyPEM.decode('ascii'))'''

def save_key(keys):
    with open('priv.pem', 'wb') as f:
        f.write(keys.exportKey())
    print('saved private key to priv.pem')
    with open('pub.pem', 'wb') as f:
        f.write(keys.public_key().export_key())
    print('saved public key to pub.pem')

def get_key():
    if not os.path.isfile('priv.pem') or not os.path.isfile('pub.pem'):
        print('Private and/or public key not found')
        keys = make_key()
        save_key(keys)
        return keys.exportKey(), keys.public_key().export_key()
    else:
        with open('priv.pem', 'r') as f:
            priv = RSA.import_key(f.read())
        print('loaded private key')
        with open('pub.pem', 'r') as f:
            pub = RSA.import_key(f.read())
        print('loaded public key')
        return priv, pub

def get_decryptor():
    key = get_key()[0]
    return PKCS1_OAEP.new(key)

'''priv, pub = get_key()
msg = 'A message for encryption'.encode()
encryptor = PKCS1_OAEP.new(pub)
encrypted = encryptor.encrypt(msg)
print(encrypted)
print("Encrypted:", binascii.hexlify(encrypted))
decry = PKCS1_OAEP.new(priv)
d_msg = decry.decrypt(encrypted)
print('decrypted:', d_msg)'''