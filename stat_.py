import requests
import json
import re

import time
import datetime
from config import TOKEN
from sql import *
import sqlite3 as sq

import telebot
from telebot import types
import pandas as pd


bot = telebot.TeleBot(TOKEN)


array_list = []



def get_datetime(block_time): #get datetime object from block_time ISO-....
    reg_f = re.search(r".\d{3}$", block_time)
    reg_f = reg_f.group(0)
    clear_dt = block_time.replace(reg_f, "")
    date_obj = datetime.datetime.strptime(clear_dt, '%Y-%m-%dT%H:%M:%S')
    return date_obj

def get_timestamp(date_obj):
    return int(datetime.datetime.timestamp(date_obj))

def get_date(timestamp):
    timestamp = int(timestamp)
    return datetime.datetime.fromtimestamp(timestamp)



def convert_account(account):
    table_name = account.replace('.', '_')
    if re.search(r"\.|\d", table_name):
        reg_num = re.search(r"\.|\d", table_name)
        reg_num = reg_num.group(0)
        table_name = table_name.replace(reg_num, '_')
    return table_name


def check_server_status():
    # TODO: choose best response time
    global url
    try:
        url = "https://wax.greymass.com"
        resp = requests.get(url)
        if resp.status_code == 200:
            server_status = "Status server: OK 200"
            resp = json.loads(resp.text)
        else:
            server_status = "Status server: Looks like server is down"
        server_time = resp['head_block_time']
        print(f'Entrypoint: {url}\nServer time: {get_datetime(server_time)}\n{server_status}\n')
    except requests.exceptions.ConnectionError as error:
        url = "https://api.waxsweden.org/v1/chain/get_info"
        resp = requests.get(url)
        if resp.status_code == 200:
            server_status = "Status server: OK 200"
            resp = json.loads(resp.text)
        else:
            server_status = "Status server: Looks like server is down"
        server_time = resp['head_block_time']
        print(f'Entrypoint: {url}\nServer time: {get_datetime(server_time)}\n{server_status}\n')
        url = "https://api.waxsweden.org"

check_server_status()

def check_exists_account(account):
    #url = f"https://api.waxsweden.org/v2/history/get_creator?account={account}"
    url = f"https://wax.eosrio.io/v2/history/get_creator?account={account}"
    out = requests.get(url)
    out = json.loads(out.text)
    try:
        if out['account'] == account:
            return True
    except KeyError:
        return False
    except requests.exceptions.SSLError:
        return Error



def get_tlm_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=alien-worlds&vs_currencies=usd&include_market_cap=false&include_24hr_vol=false&include_24hr_change=false&include_last_updated_at=false"
    out = requests.get(url)
    out = json.loads(out.text)
    return out['alien-worlds']['usd']



def check_exists_db():
    con = sq.connect("db.db")
    cur = con.cursor()
    cur.execute(f"""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER,
    account TEXT,
    notifications BOOLEAN DEFAULT 0
    )""")
    con.commit()
    con.close()

check_exists_db()


def get_tlm_staked(account):
    url = f"https://wax.eosrio.io/v2/state/get_tokens?account={account}"
    out = requests.get(url)
    out = json.loads(out.text)
    mag = out['tokens'][0]['symbol']
    vel = out['tokens'][1]['symbol']
    if mag == "MAG":
        mag = out['tokens'][0]['amount']
        if vel == "VEL":
            vel = out['tokens'][1]['amount']
            amount_tlm_staked = vel + mag
            return round(amount_tlm_staked, 4)
    else:
        return False

def _get_tlm_staked(account):
    url = f"https://wax.eosrio.io/v2/state/get_tokens?account={account}"
    out = requests.get(url)
    out = json.loads(out.text)
    sym = "symbol"
    for sym in out['tokens']:
        if sym['symbol'] == ("MAG" or "VEL"):
            print(sym)
            print(sym['symbol'], sym['amount'])
            summ = sym['amount']
            return summ



def get_cpu(account):
    #url = "http://wax.greymass.com/v1/chain/get_account"
    _url = url + "/v1/chain/get_account"
    print(f"DEBUG: Used url {_url}")
    data = {"account_name":account}
    data = json.dumps(data)
    out = requests.post(_url, data = data)
    out = json.loads(out.text)
    cpu_percent = out["cpu_limit"]['used'] / (out["cpu_limit"]['max'] / 100)
    cpu_percent = round(cpu_percent, 2)
    block_time = out['head_block_time']
    #print('Current CPU load: ', cpu_percent)
    return block_time, cpu_percent


def get_cpu_used(account):
    _url = url + "/v1/chain/get_account"
    data = {"account_name":account}
    data = json.dumps(data)
    out = requests.post(url, data = data)
    out = json.loads(out.text)
    cpu_used = out["cpu_limit"]['used']
    return cpu_used


def get_all_tx(account, pos, offset):  #pos - position -1 is last tx, offset - amount of tx max 100 per request
    _url = url + "/v1/history/get_actions"
    data = {"account_name":account,"pos":pos,"offset":offset}
    data = json.dumps(data)
    out = requests.post(_url, data = data)
    out = json.loads(out.text)
    tx = out['actions'][0]
    return tx


def get_max_tx(account):
    _url = url + "/v1/history/get_actions"
    data = {"account_name":account,"pos":-1,"offset":-1}
    data = json.dumps(data)
    out = requests.post(_url, data = data)
    out = json.loads(out.text)
    max_tx = out['actions'][0]['account_action_seq'] + 1
    return max_tx

def get_last_tlm_tx(account):
    print("DEBUG: Called func get_last_tlm_tx()")
    print("INFO: get_last_tlm_tx: Looking for a last transaction with Mined TLM\nIt may take some time...")
    _url = url + "/v1/history/get_actions"
    data = {"account_name":account,"pos":-1,"offset":-1}
    data = json.dumps(data)
    out = requests.post(_url, data = data)
    out = json.loads(out.text)
    ## TODO: if account has 0 tx return exception
    account_tx = out['actions'][0]['action_trace']['act']['account']
    if account_tx == 'alien.worlds':
        send_to_tx = out['actions'][0]['action_trace']['act']['data']['memo']
        if send_to_tx == 'ALIEN WORLDS - Mined Trilium':
            last_tx = out['actions'][0]['account_action_seq']
            return int(last_tx)
    else:
        #print("Last tx is not Mine Trilium, search...\n")
        # TODO: Correct parse last tlm acc with more than 100 tx without TLM
        #print("Total amount tx: ", get_max_tx(account))
        total_h = get_max_tx(account) // 100
        for number in range(0, total_h + 1):
            pos = get_max_tx(account) - (number * 100)
            #print("Position:", pos)
            data = {"account_name":account,"pos":pos,"offset":-100}
            data = json.dumps(data)
            out = requests.post(_url, data = data)
            out = json.loads(out.text)
            try:
                for i in range(99, -1, -1):
                    #print(f"Index tx for array: {i}\n")
                    account_tx = out['actions'][i]['action_trace']['act']['account']
                    found_tx = out['actions'][i]['account_action_seq']
                    #print("TX from:", account_tx)
                    #print("TX seq number:", found_tx)
                    if account_tx == 'alien.worlds':
                        send_to_tx = out['actions'][i]['action_trace']['act']['data']['memo']
                        if send_to_tx == 'ALIEN WORLDS - Mined Trilium':
                            last_tx = out['actions'][i]['account_action_seq']
                            return int(last_tx)
            except IndexError as error:
                print(f"ERROR: Looks like account {account} doesn't have tx with TLM")
                return None


def get_last_contact(account): # Get last contact with TLM mining for account time in UTC
    print(f"INFO: Finding last contact for {account}")
    _url = url + "/v1/history/get_actions"
    data = {"account_name":account,"pos":-1,"offset":-1}
    data = json.dumps(data)
    out = requests.post(_url, data = data)
    out = json.loads(out.text)
    ## TODO: if account has 0 tx return exception
    account_tx = out['actions'][0]['action_trace']['act']['account']
    if account_tx == 'alien.worlds':
        send_to_tx = out['actions'][0]['action_trace']['act']['data']['memo']
        if send_to_tx == 'ALIEN WORLDS - Mined Trilium':
            last_contact = out['actions'][0]['block_time']
            return get_datetime(last_contact)
    else:
        total_h = get_max_tx(account) // 100
        for number in range(0, total_h + 1):
            pos = get_max_tx(account) - (number * 100)
            data = {"account_name":account,"pos":pos,"offset":-100}
            data = json.dumps(data)
            out = requests.post(_url, data = data)
            out = json.loads(out.text)
            try:
                for i in range(99, -1, -1):
                    account_tx = out['actions'][i]['action_trace']['act']['account']
                    if account_tx == 'alien.worlds':
                        send_to_tx = out['actions'][i]['action_trace']['act']['data']['memo']
                        if send_to_tx == 'ALIEN WORLDS - Mined Trilium':
                            last_contact = out['actions'][i]['block_time']
                            return get_datetime(last_contact)
            except IndexError as error:
                print(f"ERROR: Looks like account {account} doesn't have TLM tx")
                return None
    return None


def get_tlm_for_date(account, start_time, end_time):
    print("DEBUG: Called func get_tlm_for_date()")
    #print(f'\nCalculating TLM from {start_time} to {end_time} for account {account}')
    table_name = convert_account(account)
    start_time = get_timestamp(start_time)
    end_time = get_timestamp(end_time)

    #print("Start time: ", start_time)
    #print("End time: ", end_time)
    try:
        con = sq.connect("db.db")
        con.row_factory = sq.Row
        cur = con.cursor()
        cur.execute(f"SELECT block_time, amount_tlm FROM {table_name} WHERE block_time BETWEEN {start_time} AND {end_time}")

        summary = 0
        for result in cur:
            summary += float(result['amount_tlm'])
        summary = round(summary, 4)
        print(f"{round(summary, 4)} TLM mined from {get_date(start_time)} to {get_date(end_time)}") # Architecture is not Correct
        con.close()
        return summary
    except sq.Error as error:
        print("ERROR: get_tlm_for_date() Ошибка при работе с SQLite", error)
    finally:
        if con:
            con.close()
            print("DEBUG: get_tlm_for_date() Соединение с SQLite закрыто")



def get_first_tlm_tx_db(account):
    table_name = convert_account(account)
    with sq.connect("db.db") as con:
        con.row_factory = sq.Row
        cur = con.cursor()
        cur.execute(f"SELECT block_time FROM {table_name} ORDER BY rowid ASC LIMIT 1")
        first_date = get_date(cur.fetchone()['block_time'])
        return first_date

def get_last_tlm_tx_db(account):
    try:
        table_name = convert_account(account)
        con = sq.connect("db.db")
        con.row_factory = sq.Row
        cur = con.cursor()
        print("DEBUG: get_last_tlm_tx_db() Подключен к SQLite")
        cur.execute(f"SELECT block_time FROM {table_name} ORDER BY rowid DESC LIMIT 1")
        last_tx = get_date(cur.fetchone()['block_time'])
        con.close()
        return last_tx
    except sq.Error as error:
        print("ERROR: get_last_tlm_tx_db() Ошибка при работе с SQLite", error)
    finally:
        if con:
            con.close()
            print("DEBUG: get_last_tlm_tx_db() Соединение с SQLite закрыто")





def get_tlm_range(account, pos, num):
    print("DEBUG: Called func get_tlm_range")
    table_name = convert_account(account)
    url = "https://wax.greymass.com/v1/history/get_actions"
    data = {"account_name":account,"pos":pos,"offset":num}
    data = json.dumps(data)
    out = requests.post(url, data = data)
    out = json.loads(out.text)
    dictionary = {}
    for i in range(0, num):
        account_tx = out['actions'][i]['action_trace']['act']['account']
        if account_tx == 'alien.worlds':
                send_to_tx = out['actions'][i]['action_trace']['act']['data']['memo']
                if send_to_tx == 'ALIEN WORLDS - Mined Trilium':
                    account_action_seq = out['actions'][i]['account_action_seq']
                    amount_tlm = out['actions'][i]['action_trace']['act']['data']['quantity'].replace(' TLM', '')
                    block_time = out['actions'][i]['block_time']
                    dictionary['account_action_seq'] = account_action_seq
                    dictionary['block_time'] = block_time
                    dictionary['amount_tlm'] = amount_tlm
#----------------------------------------------writing into DB--------------------------------------------------------------------------------------------
                    con = sq.connect("db.db")
                    cur = con.cursor()
                    cur.execute(f"SELECT tx_id FROM {table_name} WHERE tx_id = {dictionary['account_action_seq']}")
                    if cur.fetchone() is None:
                        cur.execute(f"INSERT INTO {table_name} VALUES (?, ?, ?)", (dictionary['account_action_seq'], get_timestamp(get_datetime(dictionary['block_time'])), dictionary['amount_tlm']))
                        con.commit()
                        con.close()
                        print(f"INFO: tx {dictionary['account_action_seq']} added into {table_name} table")
                    else:
                        print(f"WARN: tx already exists in {table_name} table")
#----------------------------------------------writing into DB--------------------------------------------------------------------------------------------


def sync_db(account):
    print("DEBUG: Called func sync_db()")
    table_name = convert_account(account)
    con = sq.connect("db.db")
    con.row_factory = sq.Row
    cur = con.cursor()
    cur.execute(f"""CREATE TABLE IF NOT EXISTS {table_name} (
    tx_id INTEGER PRIMARY KEY,
    block_time INTEGER,
    amount_tlm TEXT
    )""")
    con.commit()

    last_tx = get_last_tlm_tx(account)
    if isinstance(last_tx, int):
        cur.execute(f"SELECT tx_id FROM {table_name} WHERE tx_id = {last_tx}")
        if cur.fetchone() is None:
            cur.execute(f"SELECT tx_id FROM {table_name} ORDER BY tx_id DESC")
            if cur.fetchone() is None:
                tx_id = 0
            else:
                cur.execute(f"SELECT tx_id FROM {table_name} ORDER BY tx_id DESC")
                rows = cur.fetchone()
                tx_id = rows['tx_id']
                print(f"DB not synced with blockchain, last tx {account} in blockchain {last_tx} in DB {tx_id}")

            if (get_max_tx(account) - tx_id) > 100:
                con.close()
                print("Started long sync")
                num1 = get_max_tx(account) % 100 #Остаток от делениея на 100
                num2 = get_max_tx(account) // 100 # количество сотен
                for i in range(0, num2):
                    pos = i * 100
                    num = 100
                    get_tlm_range(account, pos, num)
                print(f"Position = {num2 * 100}, offset = {num1}")
                get_tlm_range(account, num2 * 100, num1)
            else:
                con.close()
                print("Started short sync")
                pos = rows['tx_id'] + 1
                num = last_tx - rows['tx_id']
                get_tlm_range(account, pos, num)
        else:
            con = sq.connect("db.db")
            con.row_factory = sq.Row
            cur = con.cursor()
            #cur.execute(f"SELECT tx_id FROM {table_name} WHERE tx_id = {last_tx}")
            cur.execute(f"SELECT tx_id FROM {table_name} ORDER BY tx_id DESC")
            rows = cur.fetchone()
            print(f"DB synced with blockchain {account} is {last_tx} in DB {rows['tx_id']}")
        return True
    else:
        return False


def sync_many(accounts):
    for account in accounts:
        sync_db(account)


def make_days_stats(account):
    sync_db(account)
    print(f"INFO: Called make_days_stats() {account}")

    first_date = get_first_tlm_tx_db(account).replace(minute=0, hour=0, second=0, microsecond=0)  # datetime object
    next_date = first_date + datetime.timedelta(days=1)

    while next_date != get_last_tlm_tx_db(account).replace(minute=0, hour=0, second=0, microsecond=0):
        try:
            tlm = get_tlm_for_date(account, first_date, next_date)
            date = next_date.date()
            #print(f'DEBUG: Date: {date}, first date {first_date}, next_date {next_date}')
            con = sq.connect("db.db")

            table_name = convert_account(account)
            con.row_factory = sq.Row
            cur = con.cursor()
            print("DEBUG: make_days_stats() Подключен к SQLite")

            cur.execute(f"""CREATE TABLE IF NOT EXISTS {table_name}_days (
            date TEXT,
            amount_tlm REAL
            )""")
            con.commit()

            cur.execute(f"SELECT date FROM {table_name}_days WHERE date = '{date}'")
            if cur.fetchone() is None:
                cur.execute(f"INSERT INTO {table_name}_days VALUES (?, ?)", (date, tlm))
                con.commit()
                con.close()
            else:
                print(f"WARN: tx already exists in {table_name}_days table")
            first_date = next_date
            next_date = first_date + datetime.timedelta(days=1)
        except sq.Error as error:
            print("ERROR: make_days_stats() Ошибка при работе с SQLite", error)
        finally:
            if con:
                con.close()
                print("DEBUG: make_days_stats() Соединение с SQLite закрыто")


def get_all_days_stats(account):
    make_days_stats(account)

    con = sq.connect("db.db")
    con.row_factory = sq.Row
    cur = con.cursor()

    table_name = convert_account(account)
    #con.row_factory = sq.Row
    cur = con.cursor()
    cur.execute(f"SELECT date, amount_tlm FROM {table_name}_days ORDER BY date DESC")
    ds = cur.fetchall()
    con.close()
    return ds #tuple


def get_last_7days_stats(account):
    print(f"INFO: Called get_last_7days_stats {account}")
    make_days_stats(account)

    con = sq.connect("db.db")
    con.row_factory = sq.Row
    cur = con.cursor()

    table_name = convert_account(account)
    cur = con.cursor()
    cur.execute(f"SELECT date, amount_tlm FROM {table_name}_days ORDER BY date DESC LIMIT 7")
    ds = cur.fetchall()
    con.close()
    return ds #tuple


def get_last_7days_all(accounts):
    tlm = 0
    for i in range(7):
        for account in accounts:
            tlm += get_last_7days_stats(account)[i]['amount_tlm']
        tlm += tlm
    return tlm


def get_accounts_tlm(accounts, start, end): # Получаем количество ТЛМ со всех акк за период
    total_mined = 0
    for account in accounts:
        total_mined += get_tlm_for_date(account, start, end)
    print(f"Total mined from {start} to {end}, {round(total_mined, 4)} TLM")


def get_amount_tlm_tx_for_period(account):
    sync_db(account)
    table_name = convert_account(account)
    con = sq.connect("db.db")
    #con.row_factory = sq.Row
    cur = con.cursor()
    start = get_timestamp(datetime.datetime.today() - datetime.timedelta(days=1))
    end = get_timestamp(datetime.datetime.today())

    cur.execute(f"SELECT COUNT(*) FROM {table_name} WHERE block_time BETWEEN {start} AND {end}")

    results = cur.fetchone()[0]
    return results


def get_average_tlm_for_period(account):
    sync_db(account)
    table_name = convert_account(account)
    con = sq.connect("db.db")
    #con.row_factory = sq.Row
    cur = con.cursor()
    start = get_timestamp(datetime.datetime.today() - datetime.timedelta(days=1))
    end = get_timestamp(datetime.datetime.today())

    cur.execute(f"SELECT amount_tlm FROM {table_name} WHERE block_time BETWEEN {start} AND {end}")
    print(get_date(start), get_date(end))
    result = [item[0] for item in cur.fetchall()]
    result = [float(x) for x in result]
    result = round(sum(result) / len(result), 4)
    return result


def diffrent_sync(account):
    print("INFO: Called func diffrent_sync")
    try:
        table_name = convert_account(account)
        con = sq.connect("db.db")
        con.row_factory = sq.Row
        cur = con.cursor()
        cur.execute(f"SELECT tx_id FROM {table_name} ORDER BY tx_id DESC")
        rows = cur.fetchone()
        if rows == None:
            print(f"WARN: {account} doesn't have transactions or DB is not synced")
            return False
        else:
            last_tx_db = rows['tx_id']
        con.close()
        diff = get_last_tlm_tx(account) - last_tx_db
        return diff
    except sq.OperationalError:
        print("ERROR: Looks that DB is not exists\n")
        return 0


def estimated_time_sync(account):
    diff = diffrent_sync(account)
    print("Diffrent tx", diff)
    est_time = 2 + diff * 0.03 #0.03 время синхронизации одного строчки
    est_time = int(est_time)
    return est_time


def mined_last_day(accounts):
    sync_many(accounts)
    start = datetime.datetime.today() - datetime.timedelta(days=1)
    end = datetime.datetime.today()
    total_mined = 0
    for account in accounts:
        total_mined += get_tlm_for_date(account, start, end)
    print(f"Total mined from {start} to {end}, {round(total_mined, 4)} TLM")
    return round(total_mined, 4)


def today_mined_one(call, account):
    print("DEBUG: Called func today_mined_one()")
    #start = datetime.datetime.today() - datetime.timedelta(days=1)
    start = datetime.datetime.utcnow()
    end = datetime.datetime.utcnow()
    start = start.replace(minute=0, hour=0, second=0, microsecond=0)
    end = end.replace(microsecond = 0)
    total_mined = get_tlm_for_date(account, start, end)
    print(f"Total mined from {start} to {end}, {round(total_mined, 4)} TLM")
    return start, end, round(total_mined, 4)


def mined_last_hour(accounts):
    sync_many(accounts)
    start = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    end = datetime.datetime.utcnow()
    total_mined = 0
    for account in accounts:
        total_mined += get_tlm_for_date(account, start, end)
    print(f"Total mined from {start} to {end}, {round(total_mined, 4)} TLM")
    return round(total_mined, 4)


def get_alltlm_range(start, end): #Only one day period because delta.days can't assgn other range
    delta = end - start
    for i in range(int(delta.days) - 1):
        start += datetime.timedelta(days=1)
        next_date = start + datetime.timedelta(days=1)
        get_accounts_tlm(accounts, start, next_date)


def get_accounts(user_id, i):
    con = sq.connect("db.db")
    con.row_factory = sq.Row
    cur = con.cursor()
    cur.execute("SELECT account FROM users WHERE user_id = ?", (user_id,))
    results = cur.fetchall()
    return results[i]['account']


def get_num_rows(user_id): # Получаем количество аккаунтов для данного юзера
    print('DEBUG: Called func get_num_rows')
    con = sq.connect("db.db")
    con.row_factory = sq.Row
    cur = con.cursor()
    cur.execute("SELECT user_id from users WHERE user_id = ?", (user_id,))
    num_row = cur.fetchall()
    num_row = len(num_row)
    print(num_row)
    return num_row


def get_array_user_ids():
    con = sq.connect("db.db")
    con.row_factory = sq.Row
    cur = con.cursor()
    cur.execute(f"SELECT user_id FROM users GROUP BY user_id")
    array_user_id = []
    for i in cur.fetchall():
        array_user_id.append(i['user_id'])
    return array_user_id


def all_accounts(user_id):
    accounts = []
    for i in range(0, get_num_rows(user_id)):
        account = get_accounts(user_id, i)
        accounts.append(account)
    return accounts
