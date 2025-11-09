#!/usr/bin/env python
import os
import sys
import environ
from pathlib import Path

def main():
    BASE_DIR = Path(__file__).resolve().parent
    env = environ.Env()
    environ.Env.read_env(BASE_DIR / '.env')
    ENV = env('ENV', default='dev')

    os.environ.setdefault(
        'DJANGO_SETTINGS_MODULE',
        f'config.settings.{ENV}'
    )

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
