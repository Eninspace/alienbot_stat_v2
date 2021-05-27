from stat_ import *
from notifications import *
from nft import *
from ploting import *


#---------------------------------------------------TG------------------------------------------------------------------------------------
@bot.message_handler(commands = ['show_accounts'])
def show_account(message):
    if get_num_rows(message.from_user.id) == 0:
        print(f'INFO: User {message.from_user.id} doesn\'n have accounts')
        bot.send_message(message.from_user.id, "У Вас нема аккаунтов /add_account")
    elif get_num_rows(message.from_user.id) > 0:
        markup_inline = types.InlineKeyboardMarkup() # Объект клавиатуры

        num = get_num_rows(message.from_user.id)
        print(f"DEBUG: Rows for {message.from_user.id} = ", num)
        keyboards = []
        #indexs = []
        button_all = types.InlineKeyboardButton(text = "Статистика для всех аккаунтов", callback_data = "all")
        for i in range(num):
            keyboards.append(types.InlineKeyboardButton(text = get_accounts(message.from_user.id, i), callback_data = f"id_{i}"))
            print(f"Added keyboard with for account with index {i} {get_accounts(message.from_user.id, i)}")
            #indexs.append(i)
            markup_inline.add(keyboards[i])
        markup_inline.add(button_all)
        bot.send_message(message.from_user.id, "Ваши аккаунты", reply_markup = markup_inline)


@bot.callback_query_handler(func = lambda call: call.data.startswith('id_'))
def callback_worker(call):
    index = int(call.data.replace("id_", ""))
    account = get_accounts(call.from_user.id, index)
    print("DEBUG: callback_worker for", account)

    markup_inline = types.InlineKeyboardMarkup()                                              # Объект клавиатуры
    button_ss = types.InlineKeyboardButton(text = "Статистика за 24ч", callback_data = f'24h_id_{index}')
    button_s7 = types.InlineKeyboardButton(text = "Статистика за 7 дней", callback_data = f'7d_id_{index}')
    button_nft = types.InlineKeyboardButton(text = "Показать NFT", callback_data = f'show_nfts_{index}')
    #button_del = types.InlineKeyboardButton(text = "Удалить аккаунт", callback_data = f'del_{index}')
    markup_inline.row(button_ss, button_s7)
    markup_inline.add(button_nft)
    bot.send_message(call.from_user.id, f'Аккаунт: <code>{get_accounts(call.from_user.id, index)}</code>\n CPU Load: {get_cpu(account)[1]}%', reply_markup = markup_inline, parse_mode="HTML")
    #bot.send_message(message.from_user.id, f"Аккаунт: {get_accounts(call.from_user.id, index)}", reply_markup = markup_inline)

    print("DEBUG: index =", index)
    print("Stats for user_id =", call.from_user.id)
    #bot.send_message(call.from_user.id, f"Подождите примерно {estimated_time_sync(account)} секунд")
    # TODO: # OPTIMIZE: for more requests



@bot.callback_query_handler(func = lambda call: call.data.startswith('show_nfts_'))
def callback_worker24h(call):
    index = int(call.data.replace("show_nfts_", ""))
    account = get_accounts(call.from_user.id, index)
    bot.send_message(call.from_user.id, f"NFT {account}\n{get_nft(account)}")


@bot.callback_query_handler(func = lambda call: call.data.startswith('24h_id_'))
def callback_worker24h(call):
    index = int(call.data.replace("24h_id_", ""))
    account = get_accounts(call.from_user.id, index)
    bot.send_message(call.from_user.id, f"Добавляю {diffrent_sync(account)} транзакций, подождите...")
    start, end, today_mined_tlm = today_mined_one(call, account)
    mined_usd = get_tlm_price() * today_mined_tlm
    bot.send_message(call.from_user.id, f'Аккаунт: <code>{get_accounts(call.from_user.id, index)}</code>\nСтатистика за последние 24 часа по UTC\nс {start} по {end}\n Количество майнов <code>{get_amount_tlm_tx_for_period(account)}</code>\nСредний майн: <code>{get_average_tlm_for_period(account)}</code>\n <code>{today_mined_tlm}</code> TLM Mined - $<code>{round(mined_usd, 2)}</code>', parse_mode="HTML")


@bot.callback_query_handler(func = lambda call: call.data.startswith('7d_id_'))
def callback_worker7d(call):
    bot.send_message(call.from_user.id, "Подождите...")
    index = int(call.data.replace("7d_id_", ""))
    account = get_accounts(call.from_user.id, index)
    days_7 = get_last_7days_stats(account)
    image_7d = render_7d_stat(account)
    if len(days_7) >= 7:
        #diff0 = ((days_7[0][1] / (days_7[1][1] / 100)) - 100)
        #diff0 = round(diff0, 2)
        text = f"""
{days_7[0][0]} - {days_7[0][1]} TLM\n{days_7[1][0]} - {days_7[1][1]} TLM\n{days_7[2][0]} - {days_7[2][1]} TLM\n{days_7[3][0]} - {days_7[3][1] } TLM
{days_7[4][0]} - {days_7[4][1]} TLM\n{days_7[5][0]} - {days_7[5][1]} TLM\n{days_7[6][0]} - {days_7[6][1]} TLM
        """
        bot.send_message(call.from_user.id, text, parse_mode="HTML")
        image_7d = open(image_7d, 'rb')
        bot.send_photo(call.from_user.id, image_7d)
    else:
        bot.send_message(call.from_user.id, "Меньше 7д (в разработке)", parse_mode="HTML") ## TODO: if statistics less than 7 days


@bot.callback_query_handler(func = lambda call: call.data.startswith('all'))
def callback_worker(call):
    #call.data = int(call.data.replace("id_", ""))
    accounts = all_accounts(call.from_user.id)
    bot.send_message(call.from_user.id, f"Ожидайте...")
    print("call.data =", call.data)
    print("Stats for user_id =", call.from_user.id)
    #bot.send_message(call.from_user.id, f"Подождите примерно {estimated_time_sync(account)} секунд")
    # TODO: # OPTIMIZE: for more requests
    # TODO: Add amount mine for day for all accounts
    mined_tlm = mined_last_day(accounts)
    mined_usd = get_tlm_price() * mined_tlm
    bot.send_message(call.from_user.id, f'Статистика за последние 24 часа\n <code>{mined_tlm}</code> TLM Mined - $<code>{round(mined_usd, 2)}</code>', parse_mode="HTML")




@bot.message_handler(commands = ['menu']) # TEST function
def menu(message):
    print("DEBUG: Called menu")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    itembtn1 = types.KeyboardButton('Аккаунты')
    itembtn2 = types.KeyboardButton('Настройки')
    markup.add(itembtn1, itembtn2) # callback_data = "notice_on"
    bot.send_message(message.from_user.id, "Меню", reply_markup=markup)



@bot.message_handler(commands = ['settings'])
def settings(message):
    # Using the ReplyKeyboardMarkup class
    # It's constructor can take the following optional arguments:
    # - resize_keyboard: True/False (default False)
    # - one_time_keyboard: True/False (default False)
    # - selective: True/False (default False)
    # - row_width: integer (default 3)
    # row_width is used in combination with the add() function.
    # It defines how many buttons are fit on each row before continuing on the next row.

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    itembtn1 = types.KeyboardButton('Уведомления о бездействии')
    markup.add(itembtn1) # callback_data = "notice_on"
    bot.send_message(message.from_user.id, "Настройки:", reply_markup=markup)


@bot.message_handler(content_types=['text'])
def menu(message):
    if message.text == 'Настройки':
        markup_inline = types.InlineKeyboardMarkup()                                              # Объект клавиатуры
        button_notifications = types.InlineKeyboardButton(text = "Уведомления о бездействии", callback_data = 'notifications')
        #markup_inline.row(button_account_add, button_account_del)
        markup_inline.add(button_notifications)
        bot.send_message(message.from_user.id, "Меню Настроек", reply_markup = markup_inline, parse_mode="HTML")

    elif message.text == 'Аккаунты':
        markup_inline = types.InlineKeyboardMarkup()                                              # Объект клавиатуры
        button_account_show = types.InlineKeyboardButton(text = "Мои аккаунты", callback_data = 'account_show')
        button_account_add = types.InlineKeyboardButton(text = "Добавить аккаунт", callback_data = 'account_add')
        button_account_del = types.InlineKeyboardButton(text = "Удалить аккаунт", callback_data = 'account_del')
        markup_inline.row(button_account_add, button_account_del)
        markup_inline.add(button_account_show)
        bot.send_message(message.from_user.id, "Меню Аккаунтов", reply_markup = markup_inline, parse_mode="HTML")




@bot.callback_query_handler(func = lambda call: call.data.startswith('account_'))
def callback_worker(call):
    if call.data == 'account_show':
        show_account(call)
    elif call.data == 'account_add':
        add_account(call)
    elif call.data == 'account_del':
        bot.send_message(call.from_user.id, "В разработке")


@bot.message_handler(commands = ['add_account'])
def add_account(call):
    bot.send_message(call.from_user.id, "Напиши свой аккаунт WAX")
    bot.register_next_step_handler(call.message, reg)

def reg(message):
    user_id = message.from_user.id
    account = message.text
    if check_exists_account(account) is True:
        con = sq.connect("db.db")
        con.row_factory = sq.Row
        cur = con.cursor()
        cur.execute(f"""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER,
        account TEXT,
        notifications BOOLEAN DEFAULT 0
        )""")
        con.commit()
        cur.execute(f"SELECT account FROM users WHERE account = ?", (account,))
        if cur.fetchone() is None:
            cur.execute(f"INSERT INTO users(user_id, account) VALUES (?, ?)", (user_id, account))
            con.commit()
            print(f"Account {account} added")
            bot.send_message(message.from_user.id, f"Аккаунт {account} добавлен")
        else:
            print(f"Account {account} already exists")
            bot.send_message(message.from_user.id, f"Аккаунт {account} уже существует")
        con.close()
    else:
        print(f"Аккаунт {account} не существует")
        bot.send_message(message.from_user.id, f"Аккаунт {account} не существует")



@bot.callback_query_handler(func = lambda call: True)
def callback_worker_notice(call):
    if call.data == "notifications":
        if check_notifications(call.from_user.id) == 0:
            markup_inline = types.InlineKeyboardMarkup() # Объект клавиатуры
            button_yes = types.InlineKeyboardButton(text = "Да", callback_data = "notice_on")
            button_no = types.InlineKeyboardButton(text = "Нет", callback_data = "cancel")
            markup_inline.add(button_yes, button_no)
            bot.send_message(call.from_user.id, 'Уведомления отключены. Включить уведомления?', reply_markup = markup_inline)
        elif check_notifications(call.from_user.id) == 1:
            markup_inline = types.InlineKeyboardMarkup() # Объект клавиатуры
            button_yes = types.InlineKeyboardButton(text = "Да", callback_data = "notice_off")
            button_no = types.InlineKeyboardButton(text = "Нет", callback_data = "cancel")
            markup_inline.add(button_yes, button_no)
            bot.send_message(call.from_user.id, 'Уведомления включены. Отключить уведомления?', reply_markup = markup_inline)

    elif call.data.startswith('notice_'):
        if call.data == 'notice_on':
            on_notifications(call.from_user.id)
            bot.send_message(call.from_user.id, 'Уведомления включены')
            print(f"INFO: user {call.from_user.id} turn on notifications")
        elif call.data == 'notice_off':
            off_notifications(call.from_user.id)
            bot.send_message(call.from_user.id, 'Уведомления отключены')
            print(f"INFO: user {call.from_user.id} turn off notifications")



bot.polling(none_stop=True, interval=0)






if __name__ == '__main__':
    th1 = Thread(target=run)
    th1.daemon = True
    th1.start()
#---------------------------------------------------TG------------------------------------------------------------------------------------
