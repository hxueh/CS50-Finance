#!/usr/bin/python3
import sys
import logging
from os import path
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/html/hxueh.net/Finance/")

mysecurekeypath = path.dirname(path.abspath(__file__)) + '/secure.txt'
securekey = ''
try:
    with open(mysecurekeypath, 'r') as f:
        securekey = f.readline().strip()
except:
    sys.exit(2)

from application import app as application
application.secret_key = securekey