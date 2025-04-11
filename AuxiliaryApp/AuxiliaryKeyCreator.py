from collections import namedtuple

from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA

class AuxiliaryKeyCreator():
    def __init__(self):
        Constants = namedtuple('Constants', ['LENGTH_OF_RSA_KEY', 'KEY_FORMAT', 'CIPHER_MODE', 'PATH_FOR_TO__PUBLIC_KEY_FILE'])
        self._constants = Constants(LENGTH_OF_RSA_KEY=4096, KEY_FORMAT='DER', CIPHER_MODE=AES.MODE_CTR, PATH_FOR_TO__PUBLIC_KEY_FILE=
                                        "C:/Studia/BSK/ProjektBSK/AuxiliaryApp")

    def generate_rsa_keys(self, arg):
        keypair = RSA.generate(self._constants.LENGTH_OF_RSA_KEY)
        arg['key_priv'] = keypair.export_key(format=self._constants.KEY_FORMAT)
        arg['key_pub'] = keypair.public_key().export_key(format=self._constants.KEY_FORMAT)


    def hash_pin_with_sha256(self, pin):
        pin_hash = SHA256.new(bytes(pin))
        return pin_hash

    def cipher_key_with_aes(self, pin_hash, key_priv):
        cipher = AES.new(pin_hash.digest(), AES.MODE_CTR)
        key_priv_with_aes = cipher.encrypt(key_priv)
        return key_priv_with_aes

    def write_public_key_to_file(self, key_pub):
        with open(self._constants.PATH_FOR_TO__PUBLIC_KEY_FILE + "/ProjectBSKPublicKey.key", "wb") as file:
            file.write(key_pub)

    def write_private_key_to_pendrive(self, key_priv_with_aes):
        with open("D:/ProjectBSKPrivateKey.key", "wb") as file:
            file.write(key_priv_with_aes)