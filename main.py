from decimal import Decimal
import re
import os
import sys
import pandas as pd
from utils import formatDate, normalize_facename, normalize_string_field

target_account = None
row = None
rows = None
account_names = set()
acc_res_names = {}
total_sum = 0
vectors = []
faces = {}
objects = {}

def cut_extension(filename):
    parts = filename.split('.')
    return '.'.join(parts[:-1]) if len(parts) > 1 else filename

def convert(filename, mapper = {}):
    global target_account
    global row
    global rows
    global total_sum
    global account_names
    global vectors
    global faces
    global objects

    rows = []
    row = None
    account_names = set()
    total_sum = 0
    vectors = []
    faces = {}
    objects = {}
    objects["Деньги"] = { "Объект": "Деньги", "Ед.измерения": "руб" }

    # Parse

    target_account = None

    def convert1CRowToVector(row):
        global total_sum

        acc_name = f'РС_{filename}'

        date = row['ДатаПоступило'] if ('ДатаПоступило' in row and row['ДатаПоступило']) else row['ДатаСписано']
        sender = row.get('Плательщик', None) or row['Плательщик1']
        sender_acc = row['ПлательщикСчет']
        receiver = row.get('Получатель', None) or row['Получатель1']
        receiver_acc = row['ПолучательСчет']
        transaction_sum = row['Сумма']
        comment = row['НазначениеПлатежа'] + f'. Плательщик: {sender}. Получатель: {receiver}'

        if not sender or not receiver:
            print(sender, receiver)

        if 'Взнос наличных через АТМ' in comment:
            sender = 'Касса'
        if 'Отражено по операции с картой' in comment and 'Покупка.' in comment:
            receiver = re.search(r'.+Покупка\. (.+)\..+', comment).groups()[0].strip()
        
        if sender in mapper:
            sender = mapper[sender]
        if receiver in mapper:
            receiver = mapper[receiver]

        if sender == receiver: 
            if sender_acc != target_account:
                sender += f' {sender_acc}'
            else:
                receiver += f' {receiver_acc}'
        if sender_acc == target_account:
            account_names.add(sender)
            acc_res_names[sender_acc] = acc_name
            sender = acc_name
            total_sum -= Decimal(transaction_sum)
        else:
            account_names.add(receiver)
            acc_res_names[receiver_acc] = acc_name
            receiver = acc_name
            total_sum += Decimal(transaction_sum)

        return {
            'Дата': formatDate(date),
            'Отправитель': normalize_facename(sender),
            'Получатель': normalize_facename(receiver),
            'Объект': 'Деньги',
            'Цена за шт.': '1',
            'Сумма': transaction_sum,
            'Верифицирован': 'Да',
            'Комментарий': normalize_string_field(comment),
            'Источник': 'Выписка 1С',
            # info
            'sender_acc': sender_acc,
            'receiver_acc': receiver_acc,
        }

    with open(f'input/{filename}', encoding='ansi') as f:
        f.readline()
        def parseLine(line: str):
            global target_account
            global row
            global rows
            line = line.strip()
            if target_account is None and line[:len('РасчСчет')] == 'РасчСчет':
                target_account = line[len('РасчСчет')+1:]
                print('РасчСчет', target_account)
            elif line[:6] == "Секция":
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
            
    
try:
    mappath = sys.argv[1] if 1 < len(sys.argv) else None
    df = pd.read_csv(mappath, header=None, sep='\t')
    print(df)
    mapper = pd.Series(df[1].values, index=df[0]).to_dict()
except:
    print('Empty mapper')
    mapper = {}
print()

def save_to_logos(filename, vectors, faces, objects):
    face_values = faces.values()
    object_values = objects.values()

    vectors_df = pd.DataFrame(vectors)
    vectors_df = vectors_df.sort_values('Дата')
    vectors_df[['Цена за шт.', 'Сумма']] \
      = vectors_df[['Цена за шт.', 'Сумма']].astype(float)
    vectors_df['Дата'] = pd.to_datetime(vectors_df['Дата'])
    for acc, name in acc_res_names.items():
      vectors_df.loc[vectors_df['receiver_acc'] == acc, 'Получатель'] = name
      vectors_df.loc[vectors_df['sender_acc'] == acc, 'Отправитель'] = name
    vectors_df = vectors_df.drop('receiver_acc', axis=1)
    vectors_df = vectors_df.drop('sender_acc', axis=1)

    faces_df = pd.DataFrame(face_values)
    objects_df = pd.DataFrame(object_values)

    writer = pd.ExcelWriter(f'output/logos_{cut_extension(filename)}.xlsx', engine='xlsxwriter')
    vectors_df.to_excel(writer, index=False, sheet_name='Векторы')
    faces_df.to_excel(writer, index=False, sheet_name='Лица')
    objects_df.to_excel(writer, index=False, sheet_name='Объекты')
    writer.save()

def save_to_1c(filename, rows):
    rows_df = pd.DataFrame(rows)
    rows_df.to_excel(f'output/1c_{cut_extension(filename)}.xlsx', engine='xlsxwriter', index=False)



all_vectors = []
all_objects = {}
all_faces = {}

logos_excels = []

for filename in os.listdir('input/'):
    prev_acc_res_names = acc_res_names.copy()
    convert(filename, mapper)

    all_vectors += list(filter(lambda v: (v['receiver_acc'] not in prev_acc_res_names and v['sender_acc'] not in prev_acc_res_names), vectors))
    all_faces.update(faces)
    all_objects.update(objects)

    os.makedirs('output', exist_ok=True)
    save_to_1c(filename, rows)
    logos_excels.append((filename, vectors, faces, objects))

    print('Сумма:', total_sum)
    print('Имена РС:', account_names)
    print()

for le in logos_excels:
  save_to_logos(*le)

save_to_logos('все_и_сразу', all_vectors, all_faces, all_objects)
