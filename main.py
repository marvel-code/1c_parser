from datetime import date
from decimal import Decimal
import re
import os
from sqlite3 import Date
import sys
import pandas as pd
from utils import formatDate, normalize_facename

df = pd.read_csv('input/map.csv', header=None, sep=';')
print(df)
print()
mapper = pd.Series(df[1].values, index=df[0]).to_dict()

account_names = set()
total_sum = 0

# Parse

TARGET_ACCOUNT = "40702810262000060555"

def convert1CRowToVector(row):
    global total_sum

    sender = row['Плательщик']
    sender_acc = row['ПлательщикСчет']
    receiver = row['Получатель']
    receiver_acc = row['ПолучательСчет']
    transaction_sum = row['Сумма']
    comment = row['НазначениеПлатежа']


    if 'Взнос наличных через АТМ' in comment:
        sender = 'Касса'
    if 'Отражено по операции с картой' in comment and 'Покупка.' in comment:
        receiver = re.search(r'.+Покупка\. (.+)\..+', comment).groups()[0].strip()
    if sender in mapper:
        sender = mapper[sender]
    if receiver in mapper:
        receiver = mapper[receiver]

    if sender == receiver: 
        if sender_acc != TARGET_ACCOUNT:
            sender += f' {sender_acc}'
        else:
            receiver += f' {receiver_acc}'
    if sender_acc == TARGET_ACCOUNT:
        account_names.add(sender)
        sender = 'РС'
        total_sum -= Decimal(transaction_sum)
    else:
        account_names.add(receiver)
        receiver = 'РС'
        total_sum += Decimal(transaction_sum)

    return {
        'Дата': formatDate(row['ДатаПоступило'] or row['ДатаСписано']),
        'Отправитель': normalize_facename(sender),
        'Получатель': normalize_facename(receiver),
        'Объект': 'Деньги',
        'Цена за шт.': '1',
        'Сумма': transaction_sum,
        'Верифицирован': 'Да',
        'Комментарий': row['НазначениеПлатежа'],
        'Источник': 'Выписка 1С',
    }

vectors = []
faces = {}
objects = {}
objects["Деньги"] = { "Объект": "Деньги", "Ед.измерения": "руб" }
with open(f'input/{sys.argv[1] or "kl_to_1c.txt"}', encoding='ansi') as f:
    rows = []
    row = None
    f.readline()
    def parseLine(line: str):
        global row
        global rows
        line = line.strip()
        if line[:6] == "Секция":
            row = { 'Секция': line[6:] }
        elif row is not None:
            if line[:5] == 'Конец':
                rows.append(row)
                if row['Секция'] != "РасчСчет":
                    vector = convert1CRowToVector(row)
                    if vector is not None:
                        vectors.append(vector)
                        faces[vector['Отправитель']] = { 'Лицо': vector['Отправитель'] }
                        faces[vector['Получатель']] = { 'Лицо': vector['Получатель'] }
                row = None
            else:
                key, value = line.split('=')
                row[key] = value
    while line := f.readline():
        parseLine(line)

# Save

rows_df = pd.DataFrame(rows)
vectors_df = pd.DataFrame(vectors)
faces_df = pd.DataFrame(faces.values())
objects_df = pd.DataFrame(objects.values())

os.makedirs('output', exist_ok=True)
rows_df.to_excel('output/1c.xlsx', engine='xlsxwriter', index=False)

writer = pd.ExcelWriter('output/logos.xlsx', engine='xlsxwriter')
vectors_df.to_excel(writer, index=False, sheet_name='Векторы')
faces_df.to_excel(writer, index=False, sheet_name='Лица')
objects_df.to_excel(writer, index=False, sheet_name='Объекты')
writer.save()

print()
print('Success', total_sum, account_names)
print()
