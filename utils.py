
import re

def remove_excess_spaces(string):
    return re.sub(' +', ' ', string).strip()

def bank_normalize(facename):
  def normalize_fio(s):
    FIORE = '[а-яa-zё\-]+ [а-яa-zё\-]+ [а-яa-zё\-]+'
    m = re.search(f'//({FIORE})//|^({FIORE})$|^({FIORE}) ?/|ИНН \d+ ({FIORE})$|ИНН \d+ ({FIORE})\s?/', s, re.IGNORECASE)
    if m: s = list(filter(lambda x: x, m.groups()))[0].title()
    return s
  def normalize_inn(s):
    INN = 'ИНН \d+\s+(.+)'
    m = re.search(INN, s, re.IGNORECASE)
    if m: s = list(filter(lambda x: x, m.groups()))[0]
    return s
  def normalize_ooo(s):
    OOO = 'OOO|ООО|Общество с ограниченной ответственностью'
    m = re.search(f'^(?:{OOO}) (.+)|(.+) (?:{OOO})$', s, re.IGNORECASE)
    if m: s = list(filter(lambda x: x, m.groups()))[0].upper() + ' ООО'
    return s
  def normalize_ip(s):
    IP = 'ИП|Индивидуальный предприниматель'
    m = re.search(f'^(?:{IP}) (.+)|(.+) (?:{IP})$', s, re.IGNORECASE)
    if m: s = list(filter(lambda x: x, m.groups()))[0].title() + ' ИП'
    return s
  def normalize_pao(s):
    IP = 'ПАО|Публичное акционерное общество'
    m = re.search(f'^(?:{IP}) (.+)|(.+) (?:{IP})$', s, re.IGNORECASE)
    if m: s = list(filter(lambda x: x, m.groups()))[0].upper() + ' ПАО'
    return s
  def normalize_ao(s):
    IP = 'АО|Акционерное общество'
    m = re.search(f'^(?:{IP}) (.+)|(.+) (?:{IP})$', s, re.IGNORECASE)
    if m: s = list(filter(lambda x: x, m.groups()))[0].upper() + ' АО'
    return s
  # def normalize_excess_info(s):
  #   return s.replace('\d+, (.+)', '$1')
  
  facename = normalize_fio(facename)
  facename = normalize_inn(facename)
  facename = normalize_ooo(facename)
  facename = normalize_ip(facename)
  facename = normalize_pao(facename)
  facename = normalize_ao(facename)
  return facename.strip()

def normalize_string_field(field):
  field = remove_excess_spaces(field)
  field = re.sub(r'[\\/\'"]', '', field)
  return field

def normalize_facename(facename):
    facename = bank_normalize(facename)
    facename = normalize_string_field(facename)
    return facename

def formatDate(date: str):
    d, m, y = date.split('.')
    return f'{y}.{m}.{d} 00:00:00'
