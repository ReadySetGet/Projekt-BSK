"""!@package AuxiliaryKeyCreator
It provides all the functionalities necessary from the technical perspective to execute the key generation proccess.
"""

from collections import namedtuple
import time

from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA

from OpenSSL import crypto


class AuxiliaryKeyCreator():
    """!The generator class. It realizes all the functionalities of this package."""

    def __init__(self):
        """!Constructor. It sets the constants used."""

        Constants = namedtuple('Constants', ['LENGTH_OF_RSA_KEY', 'KEY_FORMAT', 'CIPHER_MODE', 'PATH_FOR_TO__PUBLIC_KEY_FILE'])
        self._constants = Constants(LENGTH_OF_RSA_KEY=4096, KEY_FORMAT='PEM', CIPHER_MODE=AES.MODE_CBC, PATH_FOR_TO__PUBLIC_KEY_FILE=
                                        "C:/Studia/BSK/ProjektBSK/AuxiliaryApp")

    def generate_rsa_keys(self, arg):
        """!Main generator method.

        It generates the RSA keys and exports them to .pem format

        \param arg ({__setitem__}): a way of returning the keys to [AuxiliaryGUI](#AuxiliaryGUI).
        """

        self._keypair = RSA.generate(self._constants.LENGTH_OF_RSA_KEY)
        arg['key_priv'] = self._keypair.export_key(format=self._constants.KEY_FORMAT)
        arg['key_pub'] = self._keypair.public_key().export_key(format=self._constants.KEY_FORMAT)


    def hash_pin_with_sha256(self, pin):
        """!It hashes the pin provided with SHA256.

        \param pin (int): the pin provided

        \return (bytes) hash of the pin
        """

        self._pin_hash = SHA256.new(bytes(pin))
        return self._pin_hash

    def cipher_key_with_aes(self, pin_hash):
        """!It encrypts the private key with AES256 algorithm.

        \param pin_hash (bytes): hash of the pin used as AES passphrase

        \return (bytes) the encrypted private key
        """
        key_priv_with_aes = self._keypair.export_key(passphrase=pin_hash.digest(),
                                                format=self._constants.KEY_FORMAT,
                                pkcs=8,
                                protection='scryptAndAES256-CBC')
        return key_priv_with_aes

    def write_public_key_to_file(self):
        """!It writes the public key to a .pem file."""

        with open(self._constants.PATH_FOR_TO__PUBLIC_KEY_FILE + "/ProjectBSKPublicKey.pem", "wb") as file:
            key_pub_save = self._keypair.public_key().export_key(format=self._constants.KEY_FORMAT)
            file.write(key_pub_save)
        self.gen_cert()

    def write_private_key_to_pendrive(self, key_priv_with_aes):
        """!It writes the private key to a .pem file.

        \param key_priv_with_aes (bytes): the encrypted private key
        """

        with open("D:/ProjectBSKPrivateKey.pem", "wb") as file:
            file.write(key_priv_with_aes)

    def gen_cert(self):
        """!It generates a certificate based on the generated public key, needed for later PAdES digital signature, and saves it
        to a file.
        """

        timestamp_epoch_time_start = 0
        key = crypto.load_publickey(crypto.FILETYPE_PEM,
                                    open("C:/Studia/BSK/ProjektBSK/AuxiliaryApp/ProjectBSKPublicKey.pem").read())
        keyPriv = crypto.load_privatekey(crypto.FILETYPE_PEM,
                                         open("D:/ProjectBSKPrivateKey.pem").read(), self._pin_hash.digest())
        timestamp_epoch_time_end = 10 * 365 * 24 * 60 * 60
        cert_sign = crypto.X509()
        cert_sign.get_subject().CN = "Adam Zarzycki 193243"
        cert_sign.set_serial_number(int(time.time()))
        cert_sign.gmtime_adj_notBefore(timestamp_epoch_time_start)
        cert_sign.gmtime_adj_notAfter(timestamp_epoch_time_end)
        cert_sign.set_issuer(cert_sign.get_subject())
        cert_sign.set_pubkey(key)
        cert_sign.add_extensions([crypto.X509Extension(b"keyUsage", False, b"digitalSignature,nonRepudiation")])
        cert_sign.sign(keyPriv, "sha256")
        sign_cert = crypto.dump_certificate(crypto.FILETYPE_PEM, cert_sign)

        with open("certyfikat.pem", "wb") as certfile:
            certfile.write(sign_cert)
