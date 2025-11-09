from .base import *

DEBUG = True
DATABASES = {
    'default': env.db(default='sqlite:///db.sqlite3')
}
