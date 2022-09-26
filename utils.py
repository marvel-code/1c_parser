
import re

def remove_excess_spaces(string):
    return re.sub(' +', ' ', string)
