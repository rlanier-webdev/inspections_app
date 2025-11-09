from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

ENV = env('ENV', default='dev')

if ENV == 'prod':
    from .prod import *
else:
    from .dev import *
