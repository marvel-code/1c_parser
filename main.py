import re
import os
import pandas as pd
from utils import remove_excess_spaces

# Parse

def convertRowToVector(row):
    sender = row['Плательщик']
    receiver = row['Получатель']
    comment = row['НазначениеПлатежа']

    if 'Взнос наличных через АТМ' in comment:
        sender = 'Касса'
    if 'Отражено по операции с картой' in comment and 'Покупка.' in comment:
        receiver = re.search(r'.+Покупка\. (.+)\..+', comment).groups()[0].strip()

    sender = remove_excess_spaces(sender)
    receiver = remove_excess_spaces(receiver)

    return {
        'Дата': row['ДатаПоступило'] or row['ДатаСписано'],
        'Отправитель': sender,
        'Получатель': receiver,
        'Объект': 'Деньги',
        'Цена за шт.': '1',
        'Сумма': row['Сумма'],
        'Верифицирован': 'Да',
        'Комментарий': row['НазначениеПлатежа'],
        'Источник': 'Выписка 1С',
    }

vectors = []
with open('input/kl_to_1c.txt', encoding='ansi') as f:
    rows = []
    row = None
    f.readline()
    while (line := f.readline()):
        line = line.strip()
        if line[:6] == "Секция":
            row = { 'Тип': line[6:] }
        elif line[:5] == 'Конец':
            rows.append(row)
            if row['Тип'] != "РасчСчет":
                vectors.append(convertRowToVector(row))
        elif row is not None:
            key, value = line.split('=')
            row[key] = value

# Save

rows_df = pd.DataFrame(rows)
vectors_df = pd.DataFrame(vectors)

os.makedirs('output', exist_ok=True)
rows_df.to_excel('output/output.xlsx', engine='xlsxwriter')
vectors_df.to_excel('output/vectors.xlsx', engine='xlsxwriter')

print()
print('Success')
print()
