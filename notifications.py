from stat_ import *
from threading import Thread


def on_notifications(user_id):
    try:
        con = sq.connect("db.db")
        cur = con.cursor()
        print("DEBUG: Подключен к SQLite")
        cur.execute("UPDATE users SET notifications = 1 WHERE user_id = ?", (user_id,))
        con.commit()
        print("DEBUG: Запись успешно обновлена")
        cur.close()

    except sq.Error as error:
        print("ERROR: Ошибка при работе с SQLite", error)
    finally:
        if con:
            con.close()
            print("DEBUG: Соединение с SQLite закрыто")


def off_notifications(user_id):
    try:
        con = sq.connect("db.db")
        cur = con.cursor()
        print("DEBUG: Подключен к SQLite")
        cur.execute("UPDATE users SET notifications = 0 WHERE user_id = ?", (user_id,))
        con.commit()
        print("DEBUG: Запись успешно обновлена")
        cur.close()

    except sq.Error as error:
        print("ERROR: Ошибка при работе с SQLite", error)
    finally:
        if con:
            con.close()
            print("DEBUG: Соединение с SQLite закрыто")


def check_notifications(user_id):
    try:
        con = sq.connect("db.db")
        con.row_factory = sq.Row
        cur = con.cursor()
        print("DEBUG: Подключен к SQLite")
        cur.execute("SELECT notifications FROM users WHERE user_id = ?", (user_id,))
        result = cur.fetchone()['notifications']
        con.close()
        return result
    except sq.Error as error:
        print("ERROR: Ошибка при работе с SQLite", error)
    finally:
        if con:
            con.close()
            print("DEBUG: Соединение с SQLite закрыто")


def is_account_active(account):
    last_contact = get_last_contact(account)
    diff = datetime.datetime.utcnow().replace(microsecond = 0) - last_contact
    print(diff)
    if diff > datetime.timedelta(hours=1):
        print("INFO: Looks account is not active more than hour")
        return False, last_contact
    else:
        return True, last_contact


def notifications():
    while True:
        for user_id in get_array_user_ids():
            print(user_id)
            while check_notifications(user_id) == 1:
                print(f"INFO: user_id {user_id} has enabled notifications")
                for i in range(0, get_num_rows(user_id)):
                    print(f"DEBUG: Index = {i}")
                    account = get_accounts(user_id, i)
                    if is_account_active(account)[0] is False:
                        print(f"INFO: Account {account} user's {user_id} is not active")
                        bot.send_message(user_id, f"Кажется {account} не майнит уже более часа\nCPU: {get_cpu(account)[1]}%\nПоследний был в {is_account_active(account)[1]} UTC")
                time.sleep(1800)  # задержка перед отправкой нового уведомления 30 мин # TODO: config var or set



th0 = Thread(target=notifications, args=())
th0.daemon = True
th0.start()
