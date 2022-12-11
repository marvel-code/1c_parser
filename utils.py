
import re

def remove_excess_spaces(string):
    return re.sub(' +', ' ', string)

def bank_normalize(facename):
    FIORE = '[а-яa-zё\-]+ [а-яa-zё\-]+ [а-яa-zё\-]+'
    m = re.search(f'//({FIORE})//|^({FIORE})$|^({FIORE}) ?/|ИНН \d+ ({FIORE})$|ИНН \d+ ({FIORE})\s?/', facename, re.IGNORECASE)
    if m: facename = list(filter(lambda x: x, m.groups()))[0].title()
    return facename

def normalize_facename(facename):
    facename = bank_normalize(facename)
    facename = remove_excess_spaces(facename)
    facename = facename.replace('\\', '').replace('/', '')
    return facename

def formatDate(date: str):
    d, m, y = date.split('.')
    return f'{y}.{m}.{d} 00:00:00'
