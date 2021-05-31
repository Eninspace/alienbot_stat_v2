from stat_ import *

def get_nft(account): # get all nft
    #table_name = convert_account(account)
    url = f"https://wax.api.atomicassets.io/atomicassets/v1/assets?owner={account}&page=1&limit=100000&order=desc&sort=asset_id"
    out = requests.get(url)
    out = json.loads(out.text)
    return out

def get_price_nft(template_id):  # get lowerst price by template_id
    if template_id != 0:
        _url = f"https://wax.api.aa.atomichub.io/atomicmarket/v1/sales?limit=1&order=asc&sort=price&state=1&template_id={template_id}"

        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0',
        'Origin': 'https://wax.atomichub.io',
        'Referer': 'https://wax.atomichub.io',
        'Accept-Language': 'Accept-Language'
        }

        res = requests.get(_url, headers=headers)
        res = json.loads(res.text)
        price = int(res['data'][0]['listing_price']) / 100000000
        #currency = res['data'][0]['listing_symbol']
        date_price = res['data'][0]['updated_at_time'] # utc
        return price, date_price
    else:
        print('ERROR: unexpected template_id')
        return 0, 0


def create_db(account):
    table_name = convert_account(account) + "_nfts"
    con = sq.connect("db.db")
    cur = con.cursor()
    cur.execute(f"""CREATE TABLE IF NOT EXISTS {table_name} (
    asset_id INTEGER PRIMARY KEY,
    template_id INTEGER,
    name TEXT,
    time_of_receipt INTEGER,
    price REAL,
    date_price INTEGER
    )""")
    con.commit()
    con.close()


def sync_nfts(account):
    create_db(account)
    table_name = convert_account(account) + "_nfts"
    nfts_info = get_nft(account)
    amount_nfts = len(nfts_info['data'])
    for i in range(amount_nfts - 1):
        print(f'DEBUG: index {i}')
        asset_id = int(nfts_info['data'][i]['asset_id'])
        try:
            con = sq.connect("db.db")
            cur = con.cursor()
            print("DEBUG: Connected to SQLite")

            cur.execute(f"SELECT asset_id FROM {table_name} WHERE asset_id = {asset_id}")
            if cur.fetchone() is None:
                try:
                    template_id = int(nfts_info['data'][i]['template']['template_id'])
                except TypeError:
                    template_id = 0
                    print('ERROR: unexpected template_id')

                name = nfts_info['data'][i]['name']
                time_of_receipt = int(nfts_info['data'][i]['updated_at_time']) # utc when this nft was get in account  # updated_at_time
                price, date_price = get_price_nft(template_id)
                cur.execute(f"INSERT INTO {table_name} VALUES (?, ?, ?, ?, ?, ?)", (asset_id, template_id, name, time_of_receipt, price, date_price))
                con.commit()
                con.close()
                print(f"INFO: nft {asset_id} added into {table_name} table")
            else:
                print(f"WARN: nft {asset_id} already exists in {table_name} table")  # TODO: ask for update
                # cur.execute(f"UPDATE users SET nfts = '{nfts}' WHERE account = ?", (account,))
                # con.commit()
                # print("DEBUG: Updated")
                # cur.close()
        except sq.Error as error:
            print("ERROR: Ошибка при работе с SQLite", error)
        finally:
            if con:
                con.close()
                print("DEBUG: Соединение с SQLite закрыто")


def get_nfts(account):
    create_db(account)
    table_name = convert_account(account) + "_nfts"
    try:
        con = sq.connect("db.db")
        cur = con.cursor()
        print("DEBUG: Connected to SQLite")
        cur.execute(f"SELECT name, asset_id, time_of_receipt, price, date_price FROM {table_name}")
        result = cur.fetchall()
        con.close()
        return result
    except sq.Error as error:
        print("ERROR: Ошибка при работе с SQLite", error)
    finally:
        if con:
            con.close()
            print("DEBUG: Соединение с SQLite закрыто")


def get_available_claim(account):
    _url = "https://wax.pink.gg/v1/chain/get_table_rows"
    payload = {
        "json": True,
        "code": "m.federation",
        "scope": "m.federation",
        "table": "claims",
        "table_key": "",
        "lower_bound": account,
        "upper_bound": None,
        "index_position": 1,
        "key_type": "",
        "limit": "1",
        "reverse": False,
        "show_payer": False
    }
    payload = json.dumps(payload)
    res = requests.post(_url, data=payload)
    if res.status_code == 200:
        if json.loads(res.text)['rows'][0]['miner'] == account:
            print(account)
            return True
        else:
            return False
    else:
        print('ERROR: get_available_claim')
        return False

print(get_available_claim("w4ee4.wam"))
# TODO: cycle parsing nfts
# OPTIMIZE: searching new nfts
# TODO: notifications for new finded nfts
