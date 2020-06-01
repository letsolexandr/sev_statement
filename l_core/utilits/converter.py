##import sys
import subprocess
import re

##import os

__all__ = ['LibreOfficeConverter']


class LibreOfficeError(Exception):
    def __init__(self, output):
        self.output = output


class LibreOfficeConverter(object):

    @classmethod
    def convert_to_pdf_old(cls, source, folder, timeout=None):

        args = ['libreoffice', '--headless', '--convert-to', 'pdf:writer_web_pdf_Export', '--outdir', folder, source]
        ##print(str(args))

        process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        ##print(process.stdout)
        filename = re.search('-> (.*?) using filter', process.stdout.decode())

        if filename is None:
            raise LibreOfficeError(process.stdout.decode())
        else:
            return filename.group(1)

    @classmethod
    def convert_to_pdf(cls, source, output, timeout=None):
        args = ['doc2pdf', '-o', output, source]
        print(' '.join(args))
        subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
