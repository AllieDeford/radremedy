"""
config.py

Looks for the RAD_PRODUCTION variable and creates path to database 
"""
import os
_basedir = os.path.abspath(os.path.dirname(__file__))

if 'RAD_PRODUCTION' in os.environ:
    DEBUG = False
else:
    DEBUG = True

if 'RAD_PRODUCTION' is os.environ:
    pass
else:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, './rad/rad.db')
