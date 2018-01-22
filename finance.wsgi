#!/usr/bin/python3
import sys
import logging
from os import path
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/html/hxueh.net/Finance/")

secretkeypath = path.dirname(path.abspath(__file__)) + '/secret.txt'
secretkey = ''
try:
    with open(secretkeypath, 'r') as f:
        secretkey = f.readline().strip()
except:
    sys.exit(2)

from application import app as application
application.secret_key = secretkey