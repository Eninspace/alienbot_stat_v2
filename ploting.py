import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sqlite3 as sq
from stat_ import *
import matplotlib.pyplot as plt
import string
import random
import os

plt.switch_backend('agg')


S = 4  # number of characters in the string.
# call random.choices() string module to find the string in Uppercase + numeric data.
ran = ''.join(random.choices(string.ascii_lowercase + string.digits, k = S))
ran = str(ran)  # print the random data


def render_7d_stat(account):
    ld7 = get_last_7days_stats(account)
    date_range = [ld7[i]['date'] for i in range(7)]
    date_range = date_range[::-1] #reversing using list slicing
    amount_tlm_range = [ld7[i]['amount_tlm'] for i in range(7)]
    amount_tlm_range = amount_tlm_range[::-1] #reversing using list slicing

    date_range = pd.to_datetime(date_range)
    DF = pd.DataFrame()
    DF['value'] = amount_tlm_range
    DF = DF.set_index(date_range)
    plt.plot(DF)
    plt.gcf().autofmt_xdate()
    file_name = f'{ran}.png'
    plt.savefig(file_name)
    return file_name


def del_images():
    dir_name = os.getcwd()
    for item in os.listdir(dir_name):
        if item.endswith(".png"):
            os.remove(os.path.join(dir_name, item))
# def tr():
#     con = sq.connect("db.db")
#     con.row_factory = sq.Row
#     cur = con.cursor()
#     cur.execute(f"SELECT ammount_tlm FROM ohxdm_wam")
#     array_ammount_tlm = []
#     for i in cur.fetchall():
#         array_ammount_tlm.append(i['ammount_tlm'])
#     return array_ammount_tlm
#
# def dr():
#     con = sq.connect("db.db")
#     con.row_factory = sq.Row
#     cur = con.cursor()
#     cur.execute(f"SELECT block_time FROM ohxdm_wam")
#     array_block_time = []
#     for i in cur.fetchall():
#         array_block_time.append(i['block_time'])
#     return array_block_time
