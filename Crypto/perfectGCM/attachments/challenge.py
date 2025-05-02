import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from secret import FLAG
import json

# not sure if AES GCM is secure enough, so I've added a custom verification, 
# just to be sure the flag is perfectly encrypted

def encrypt_flag():
    key = os.urandom(16)
    aes = AES.new(key, AES.MODE_GCM)
    flag = pad(FLAG.encode(), 16)
    encrypted = aes.encrypt(flag)
    return encrypted, key

def decrypt(encrypted_flag, key):
    aes = AES.new(key, AES.MODE_GCM)
    decrypted = aes.decrypt(encrypted_flag)
    return decrypted

def verify_encryption(encrypted_flag):
    flag = FLAG.encode()
    for i in range(len(flag)):
        if not (flag[i] ^ encrypted_flag[i]):
            return False
    return True

def challenge(received_json):
    response_json = {}
    if 'action' in received_json: 
        if received_json['action'] == 'encrypt_flag':
            enc, key = encrypt_flag()
            if verify_encryption(enc):
                response_json['enc'] = enc.hex()
            else:
                response_json['enc'] = 'try again'
        elif received_json['action'] == 'decrypt':
            if 'enc' in received_json and 'key' in received_json:
                response_json['dec'] = decrypt(bytes.fromhex(received_json['enc']), bytes.fromhex(received_json['key']))
            else:
                response_json['error'] = 'invalid decrypt request'
        else:
            response_json['error'] = 'invalid action request' 
    else:
        response_json['error'] = 'no action specified'
    return response_json  
