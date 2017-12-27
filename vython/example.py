import importer
importer.install_hook()

import pip
import requests

assert pip.main(['show', 'pip']) == 0

print(requests.get('https://google.com'))
