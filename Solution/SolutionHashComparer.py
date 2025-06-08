"""!@package SolutionHashComparer
It realizes all the functionalities needed for the verification process.
"""

from collections import namedtuple

from Crypto.PublicKey import RSA
from pyhanko.keys import load_cert_from_pemder
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko_certvalidator import ValidationContext


class SolutionHashComparer():
    """!The verifier class. It realizes all the functionalities of this package."""

    def __init__(self):
        """!Constructor. It sets the constants used."""

        Constants = namedtuple('Constants',
                               ['LENGTH_OF_RSA_KEY', 'KEY_FORMAT', 'PATH_FOR_PUBLIC_KEY'])
        self._constants = Constants(LENGTH_OF_RSA_KEY=4096, KEY_FORMAT='PEM',
                                    PATH_FOR_PUBLIC_KEY="C:/Studia/BSK/ProjektBSK/AuxiliaryApp/ProjectBSKPublicKey.pem")
        self._public_key = None
        self._file_path = None
        self._file_name = None
        self._signature = None
        self._hashed_file = None

    def set_file(self, path, name):
        """!A setter for all pdf-related information.

        \param path (str): path to the pdf, without its name
        \param file (str): name of the pdf
        """

        self._file_path = path
        self._file_name = name

    def set_public_key(self):
        """!It loads the public key and its certificate from a file."""

        with open(self._constants.PATH_FOR_PUBLIC_KEY, "rb") as file:
            data = file.read()
            self._public_key = RSA.import_key(data)

        root_cert = load_cert_from_pemder("C:/Studia/BSK/ProjektBSK/AuxiliaryApp/certyfikat.pem")
        self._vc = ValidationContext(trust_roots=[root_cert])

    def verify(self):
        """!It validates the signature, based on the public key and certificate loaded by `set_public_key()` method
        It then prints the process' details to the console.

        \return  1: the signature is valid
        \return  0: the signature is invalid
        \return -1: the chosen file has no signature to verify
        """

        with open(self._file_path + self._file_name, 'rb') as doc:
            self._r = PdfFileReader(doc, strict=False)
            if len(self._r.embedded_signatures) == 0:
                return -1
            self._sig = self._r.embedded_signatures[0]
            status = validate_pdf_signature(self._sig, self._vc)
            print(status.pretty_print_details())
            if status.bottom_line:
                return 1

            return 0




