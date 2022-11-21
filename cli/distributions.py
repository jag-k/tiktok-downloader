import json
import os.path
from distutils.dist import Distribution
from sys import stderr

from app.constants import PROJECT_PATH

__all__ = ['dist']
PROJECT_PATH.cwd()

os.chdir(PROJECT_PATH)

ext = {
    'license': 'MIT',
}
ignore_fields = ['readme', 'packages']


def author_extractor(field: list[str] = None) -> dict:
    if not field:
        return {}
    author = field[0]
    if ' <' in author and author.endswith('>'):
        name, email = author.split(' <')
        email = email[:-1]

        return {
            'author': name,
            'maintainer': name,
            'author_email': email,
            'maintainer_email': email,
        }
    return {'author': author, 'maintainer': author}


extra_fields = {
    'authors': author_extractor
}

with (PROJECT_PATH / 'pyproject.toml').open('r') as pyproject:
    parse = False
    while True:
        line = pyproject.readline().strip()
        if not line:
            break

        if line == '[tool.poetry]':
            parse = True
            continue

        if parse:
            if line.startswith('['):
                parse = False
                break
            print(line, file=stderr)
            key, value = map(str.strip, line.split('=', 1))
            if key in ignore_fields:
                continue
            value = json.loads(value)
            if key in extra_fields:
                ext.update(extra_fields[key](value))
            else:
                ext[key] = value.strip('"')

dist = Distribution(ext)
