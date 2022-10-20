
import re

def remove_excess_spaces(string):
    return re.sub(' +', ' ', string)

def normalize_facename(facename):
    return remove_excess_spaces(facename).replace('\\', '/')

def formatDate(date: str):
    d, m, y = date.split('.')
    return f'{y}.{m}.{d} 00:00:00'
