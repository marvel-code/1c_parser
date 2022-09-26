
with open('input/kl_to_1c.txt', encoding='ansi') as f:
    rows = []
    row = None
    vectors = []
    f.readline()
    while (line := f.readline()):
        line = line.strip()
        if line[:6] == "Секция":
            row = { 'Тип': line[6:] }
        elif line[:5] == 'Конец':
            rows.append(row)
            if row['Тип'] != "РасчСчет":
                vectors.append({
                    'Дата': row['ДатаПоступило'] or row['ДатаСписано'],
                    'Отправитель': row['Плательщик'],
                    'Получатель': row['Получатель'],
                    'Объект': 'Деньги',
                    'Цена за шт.': '1',
                    'Сумма': row['Сумма'],
                    'Верифицирован': 'Да',
                    'Комментарий': row['НазначениеПлатежа'],
                    'Источник': 'Выписка 1С',
                })
        elif row is not None:
            key, value = line.split('=')
            row[key] = value

import os
import sys
import pandas as pd

rows_df = pd.DataFrame(rows)
vectors_df = pd.DataFrame(vectors)

os.makedirs('output')
rows_df.to_excel('output/output.xlsx', engine='xlsxwriter')
vectors_df.to_excel('output/vectors.xlsx', engine='xlsxwriter')
