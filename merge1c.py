from os import listdir
from os.path import isfile, join

mypath = join('region', '4547')
onlyfiles = [join(mypath, f) for f in listdir(mypath) if isfile(join(mypath, f))]

with open(mypath + '.txt', 'w', encoding='ansi') as fout:
    for f in onlyfiles:
        with open(f, 'r', encoding='ansi') as fin:
          fout.writelines(fin.readlines())