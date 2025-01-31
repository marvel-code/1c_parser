from decimal import Decimal
import re
import os
import sys
import pandas as pd
from utils import formatDate, normalize_facename, normalize_string_field
import platform
import json


start_balance = None
start_date = None
end_date = None
target_acc = None
row = None
rows = None
account_names = set()
acc_res_names = {}
total_sum = 0
vectors = []
faces = {}
objects = {}

def make_acc_id(inn, acc):
    return f"{inn}_{acc}"

def cut_extension(filename):
    parts = filename.split('.')
    return '.'.join(parts[:-1]) if len(parts) > 1 else filename

def convert(filename, mapper = {}):
    global target_acc
    global row
    global rows
    global total_sum
    global account_names
    global vectors
    global faces
    global objects
    global start_balance
    global start_date
    global end_date

    rows = []
    row = None
    account_names = set()
    total_sum = 0
    start_balance = None
    vectors = []
    faces = {}
    objects = {}
    objects["Деньги"] = { "Объект": "Деньги", "Ед.измерения": "руб" }

    # Parse

    target_acc = None
    start_date = None
    end_date = None

    def fetch_sender_and_receiver(row, target_acc_name):
        sender_acc = row['ПлательщикСчет']
        sender_inn = row['ПлательщикИНН']
        receiver_acc = row['ПолучательСчет']
        receiver_inn = row['ПолучательИНН']
        sender_id = make_acc_id(sender_inn, sender_acc)
        receiver_id = make_acc_id(receiver_inn, receiver_acc)
        comment = row['НазначениеПлатежа']
        sender_orig = row.get('Плательщик', None) or row['Плательщик1']
        receiver_orig = row.get('Получатель', None) or row['Получатель1']
        sender = sender_orig
        receiver = receiver_orig

        # Remove banned symbols
        sender = sender.replace('/', '')
        receiver = receiver.replace('/', '')

        # Add marker for target account name
        # print(sender_acc == target_acc, sender_acc, target_acc)
        # print(receiver_acc == target_acc, receiver_acc, target_acc)
        # if sender_acc == target_acc: sender = f'__{sender_orig}'
        # if receiver_acc == target_acc: receiver = f'__{sender_orig}'
        
        return sender, sender_inn, sender_acc, receiver, receiver_inn, receiver_acc, comment

    def convert1CRowToVector(row):
        global total_sum
        global start_balance

        target_acc_name = f'РС_{cut_extension(filename)}'

        date = row.get('ДатаПоступило', row.get('ДатаКонца', None)) or row.get('ДатаСписано', row.get('ДатаНачала', None)) # мб ДатаНачала ДатаКонца не нужно, тк относится к секции, а не транзакции
        transaction_sum = row['Сумма']
        sender, sender_inn, sender_acc, receiver, receiver_inn, receiver_acc, comment = fetch_sender_and_receiver(row, target_acc_name)

        # total_sum upd
        if sender_acc == target_acc:
            total_sum -= Decimal(transaction_sum)
        else:
            total_sum += Decimal(transaction_sum)

        return {
            'Дата': formatDate(date),
            'Отправитель': sender,
            'Получатель': receiver,
            'Объект': 'Деньги',
            'Цена за шт.': '1',
            'Сумма': transaction_sum,
            'Верифицирован': 'Да',
            'Комментарий': normalize_string_field(comment),
            'Источник': 'Выписка 1С',
            # info
            'sender_acc': sender_acc,
            'receiver_acc': receiver_acc,
            'sender_id': make_acc_id(sender_inn, sender_acc),
            'receiver_id': make_acc_id(receiver_inn, receiver_acc),
        }

    with open(f'input/{filename}', encoding=('ansi' if platform.system().lower() == 'windows' else 'windows-1251')) as f:
        f.readline()
        def parseLine(line: str):
            global target_acc
            global row
            global rows
            global start_balance
            global start_date
            global end_date
            line = line.strip()
            if target_acc is None and line[:len('РасчСчет')] == 'РасчСчет':
                target_acc = line[len('РасчСчет')+1:]
                # print('РасчСчет', target_acc)
            if start_date is None and line[:len('ДатаНачала')] == "ДатаНачала":
                start_date = line[len('ДатаНачала')+1:]
                print('ДатаНачала', start_date)
            if end_date is None and line[:len('ДатаКонца')] == "ДатаКонца":
                end_date = line[len('ДатаКонца')+1:]
                print('ДатаКонца', end_date)
                
            if start_balance is None and line[:len('НачальныйОстаток')] == 'НачальныйОстаток': 
              start_balance = Decimal(line[len('НачальныйОстаток')+1:])
              print('НачальныйОстаток', start_balance)
            elif line[:6] == "Секция":
                row = { 'Секция': line[6:] }
            elif row is not None:
                if line[:5] == 'Конец':
                    rows.append(row)
                    if row['Секция'] != "РасчСчет":
                        try:
                          vector = convert1CRowToVector(row)
                        except Exception as ex:
                          json.dump(row, open('output/failed_row.json', 'w'), indent=2, ensure_ascii=False)
                          raise ex
                        if vector is not None:
                            vectors.append(vector)
                            faces[vector['Отправитель']] = { 'Лицо': vector['Отправитель'] }
                            faces[vector['Получатель']] = { 'Лицо': vector['Получатель'] }
                    row = None
                else:
                    delimiter_index = line.find('=')
                    key, value = line[:delimiter_index], line[delimiter_index+1:]
                    row[key] = value
        while line := f.readline():
            parseLine(line)
            
print("---")
print('Platform:', platform.system())
try:
    mappath = sys.argv[1] if 1 < len(sys.argv) else None
    df = pd.read_csv(mappath, header=None, sep='\t')
    print(df)
    mapper = pd.Series(df[1].values, index=df[0]).to_dict()
except Exception as ex:
    print('Empty mapper')
    print(ex)
    mapper = {}
print("---")
print()

def print_balance_by_transactions(filename, vectors, target_acc):
  rows = []
  balance = 0
  for v in vectors:
    if v['receiver_acc'] == str(target_acc):
      balance += Decimal(v['Сумма'])
    elif v['sender_acc'] == str(target_acc):
      balance -= Decimal(v['Сумма'])
    rows.append(dict(list(v.items()) + list({ 'balance': float(balance) }.items())))
  
  df = pd.DataFrame(rows)
  df.to_excel(f'output/1c_{cut_extension(filename)}_остатки.xlsx', engine='xlsxwriter', index=False)


def save_to_logos(filename, vectors, faces, objects):
    # print_balance_by_transactions(filename, vectors, 40702810301500121718)

    face_values = faces.values()
    object_values = objects.values()

    vectors_df = pd.DataFrame(vectors)
    vectors_df = vectors_df.sort_values('Дата')
    vectors_df[['Цена за шт.', 'Сумма']] \
      = vectors_df[['Цена за шт.', 'Сумма']].astype(float)
    vectors_df['Дата'] = pd.to_datetime(vectors_df['Дата'])
    for acc_id, name in acc_res_names.items():
      vectors_df.loc[vectors_df['receiver_id'] == acc_id, 'Получатель'] = name
      vectors_df.loc[vectors_df['sender_id'] == acc_id, 'Отправитель'] = name
    vectors_df = vectors_df.drop('receiver_acc', axis=1)
    vectors_df = vectors_df.drop('sender_acc', axis=1)
    vectors_df = vectors_df.drop('receiver_id', axis=1)
    vectors_df = vectors_df.drop('sender_id', axis=1)

    faces_df = pd.DataFrame(face_values)
    objects_df = pd.DataFrame(object_values)

    writer = pd.ExcelWriter(f'output/logos_{cut_extension(filename)}.xlsx', engine='xlsxwriter')
    vectors_df.to_excel(writer, index=False, sheet_name='Векторы')
    faces_df.to_excel(writer, index=False, sheet_name='Лица')
    objects_df.to_excel(writer, index=False, sheet_name='Объекты')
    writer.close()

def save_to_1c(filename, rows):
    rows_df = pd.DataFrame(rows)
    rows_df.to_excel(f'output/1c_{cut_extension(filename)}.xlsx', engine='xlsxwriter', index=False)



all_vectors = []
all_objects = {}
all_faces = {}

logos_excels = []

for filename in os.listdir('input/'):
    if filename.startswith('.'):
        continue
    print(filename)

    prev_acc_res_names = acc_res_names.copy()
    convert(filename, mapper)

    all_vectors += list(filter(lambda v: (v['receiver_acc'] not in prev_acc_res_names and v['sender_acc'] not in prev_acc_res_names), vectors))
    all_faces.update(faces)
    all_objects.update(objects)

    os.makedirs('output', exist_ok=True)
    # save_to_1c(filename, rows)
    # if len(vectors) > 0:
    #   logos_excels.append((filename, vectors, faces, objects))

    # print('Сумма:', total_sum)
    # print('Остаток:', start_balance + total_sum)
    # print('Имена РС:', account_names)
    print()

# for le in logos_excels:
#   save_to_logos(*le)

save_to_logos('все_и_сразу', all_vectors, all_faces, all_objects)
