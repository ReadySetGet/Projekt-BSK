"""!@package SolutionPDFSigner
It provides all the functionalities necessary from the technical perspective to execute the signing proccess.
"""

import os
from collections import namedtuple

from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from pyhanko.pdf_utils.reader import PdfFileReader

from pyhanko.sign import signers
from pyhanko.sign.fields import SigSeedSubFilter, append_signature_field, SigFieldSpec
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter


class SolutionPDFSigner():
    """!The signer class. It realizes all the functionalities of this package."""

    def __init__(self):
        """!Constructor. It sets the used constants and loads the encrypted private key from a file."""

        Constants = namedtuple('Constants',
                               ['LENGTH_OF_RSA_KEY', 'KEY_FORMAT', 'CIPHER_MODE', 'PATH_FOR_SIGNED_FILES', 'PATH_TO_PRIVATE_KEY'])
        self._constants = Constants(LENGTH_OF_RSA_KEY=4096, KEY_FORMAT='PEM', CIPHER_MODE=AES.MODE_CBC,
                                    PATH_FOR_SIGNED_FILES="C:/Studia/BSK/ProjektBSK/Solution/", PATH_TO_PRIVATE_KEY="D:/ProjectBSKPrivateKey.pem")

        self._path_to_ske = self._constants.PATH_TO_PRIVATE_KEY
        with open(self._path_to_ske, "rb") as file:
            self._signing_key_encrypted = file.read()
        self._signing_key = None
        self._file_to_sign_path = None
        self._file_to_sign = None
        self._hashed_pin = None
        self._hashed_file = None
        self._signature = None

    def set_file(self, path, file):
        """!A setter for all pdf-related information.

        \param path (str): path to the pdf, without its name
        :param file (str): name of the pdf
        """

        self._file_to_sign_path = path
        self._file_to_sign = file

    def hash_pin(self, pin):
        """!It hashes the pin provided.

        \param pin (int): pin
        """
        self._hashed_pin = SHA256.new(bytes(pin))

    def decrypt(self):
        """!It decrypts the private key the hash of the pin provided.

        \return (bool) whether the key was decrypted correctly or not (in other words, if the pin was correct)
        """

        try:
            self._signing_key = RSA.import_key(self._signing_key_encrypted, self._hashed_pin.digest())
            return True
        except:
            return False


    def prepare_file(self):
        """!It conducts all the necessary preparations before signing the chosen pdf: add a signature field to the pdf,
        sets the signature type to PAdES, and initializes an adequate PAdES signer object.

        \return   1: the method succeeded
        \return   0: pdf has already been signed
        \return  -1: no writing permissions
        """

        flag = False
        with open(self._file_to_sign_path + self._file_to_sign, 'rb') as doc:
            rd = PdfFileReader(doc)
            if len(rd.embedded_signatures) > 0:
                return 0

        try:
            with open(self._file_to_sign_path + self._file_to_sign, 'rb+') as doc:
                w = IncrementalPdfFileWriter(doc, strict=False)
                append_signature_field(w, SigFieldSpec(sig_field_name="Signature", on_page=-1, box=(10, 10, 500, 100)))
                w.write_in_place()
        except PermissionError:
            return -1

        self._cms_signer = signers.SimpleSigner.load(
            self._constants.PATH_TO_PRIVATE_KEY, "C:/Studia/BSK/ProjektBSK/AuxiliaryApp/certyfikat.pem",
            key_passphrase=self._hashed_pin.digest()
        )

        self._signature_meta = signers.PdfSignatureMetadata(
            field_name='Signature', md_algorithm='sha256',
            subfilter=SigSeedSubFilter.PADES,
            use_pades_lta=False
        )
        return 1

    def sign(self):
        """!It signs and saves the pdf, using setting set in the `prepare_file()` method."""

        with open(self._file_to_sign_path + self._file_to_sign, 'rb') as inf:
            w = IncrementalPdfFileWriter(inf, strict=False)
            with open('../pdfs/signed'+self._file_to_sign, 'wb') as outf:
                signers.sign_pdf(
                    w, signature_meta=self._signature_meta, signer=self._cms_signer,
                    output=outf
                )

        os.remove(self._file_to_sign_path + self._file_to_sign)






