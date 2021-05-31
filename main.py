from tg import *
from stat_ import *
from notifications import *

if __name__ == '__main__':
    reg_accounts_from_file(get_accounts_from_config())

    th0 = Thread(target=run_bot, args=())
    #th0.daemon = True
    th0.start()

    th1 = Thread(target=notifications, args=())
    th1.daemon = True
    th1.start()

    th2 = Thread(target=sync, args=())
    th2.daemon = True
    th2.start()
