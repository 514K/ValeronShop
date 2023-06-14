from telebot import *
import sqlite3
import pyqiwi

from threading import Thread

bot = TeleBot('TOKEN')


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    keyboard = types.ReplyKeyboardMarkup()
    key_myAcc = types.KeyboardButton("Аккаунт")
    key_price = types.KeyboardButton("Товары")
    key_buy = types.KeyboardButton("Купить")
    key_topup = types.KeyboardButton("Пополнить")
    keyboard.add(key_myAcc, key_price, key_buy, key_topup, row_width=2)

    try:
        sqlite_connection = sqlite3.connect('bot.db')
        cursor = sqlite_connection.cursor()
        # ДЛЯ НАЧАЛА ПРОВЕРЯЕМ, ЕСТЬ ЛИ ЭТОТ КЛИЕНТ
        cursor.execute("SELECT id_client FROM users WHERE id_client={};".format(
            message.from_user.id))
        # ЕСЛИ НЕТ
        sas = cursor.fetchall()
        if len(sas) == 0:
            cursor.execute("INSERT INTO users (id_client, name, moneys) VALUES (?, ?, ?)", (str(
                message.from_user.id), str(message.from_user.username), 0))

        

        sqlite_connection.commit()
        sqlite_connection.close()

    except:
        pass

    if message.text == "/start":
        bot.send_message(message.from_user.id, "Добро пожаловать в ValeronShop!", reply_markup=keyboard)
    elif message.text == "Аккаунт":
        # ТУТ ОБРАБОТКА ИЗ БАЗЫ ДАННЫХ ПО id ЮЗВЕРЯ

        try:
            sqlite_connection = sqlite3.connect('bot.db')
            cursor = sqlite_connection.cursor()
            msg = "ID: {}\nUsername: {}\nBalance: {:.2f}".format(
                message.from_user.id, message.from_user.username, getBalance(message.from_user.id))
            bot.send_message(message.from_user.id, msg, reply_markup=keyboard)
                
            sqlite_connection.commit()
            sqlite_connection.close()

        except Exception as err:
            print(err)
            pass
        

    elif message.text == "Товары":
        # ТУТ ОБРАБОТКА ИЗ БАЗЫ ДАННЫХ С ТОВАРАМИ
        try:
            sqlite_connection = sqlite3.connect('bot.db')
            cursor = sqlite_connection.cursor()
            cursor.execute("SELECT Name, Description, Count, Price FROM products")
            products = cursor.fetchall()
            msg = ""
            for i in products:
                msg = msg + "<b>" + str(i[0]) + "</b>\n" + str(i[1]) + "\nPrice: " + "{:.2f}".format(i[3]) + " RUB\n" 
                if i[2] == -1:
                    msg = msg + "Count: 99"
                else:
                    msg = msg + "Count: " + i[2]
                msg = msg + "\n=====================================\n\n"
            print(msg)
            bot.send_message(message.from_user.id, msg, parse_mode="HTML")
        except Exception as err:
            print(err)
            pass

    elif message.text == "Купить":
        # ТУТ ВЫБОР ТОВАРА И ОБРАБОТКА ПОКУПКИ, СЧЕТ ЮЗВЕРЯ ЕСТЬ В БАЗЕ
        try:
            sqlite_connection = sqlite3.connect('bot.db')
            cursor = sqlite_connection.cursor()
            kb = types.InlineKeyboardMarkup()
            cursor.execute("SELECT Name, Description, Count, id, Price FROM products WHERE Count<>0")
            products = cursor.fetchall()
            for i in products:
                kb.add(types.InlineKeyboardButton(text=str(i[0]) + ", {:.2f} RUB".format(i[4]), callback_data=str(i[3])))
            bot.send_message(message.from_user.id, "Выберите товар", reply_markup=kb)
        except Exception as err:
            print(err)
            pass
    elif message.text == "Пополнить":
        # ТУТ ВЫДАЧА ТЕЛЕФОНА И КОДА ДЛЯ ЮЗВЕРЯ ДЛЯ ПОПОЛНЕНИЯ КИВИ
        try:
            
            sqlite_connection = sqlite3.connect('bot.db')
            cursor = sqlite_connection.cursor()

            # ДЛЯ НАЧАЛА ПРОВЕРЯЕМ, ЕСТЬ ЛИ ЭТОТ КЛИЕНТ
            cursor.execute("SELECT id_client FROM users WHERE id_client={};".format(message.from_user.id))
            if len(cursor.fetchall()) == 0:
                cursor.execute("INSERT INTO users (id_client, name) VALUES ({}, {})".format(message.from_user.id, message.from_user.username))

            cursor.execute("SELECT id FROM payments WHERE id_client=? AND status='wait'", (message.from_user.id, ))

            payid = cursor.fetchall()
            if len(payid) >= 1:
                print(payid)
                payid = payid[0][0]
            else:
                cursor.execute("INSERT INTO payments (id_client, status) VALUES ({}, 'wait');".format(message.from_user.id))
                payid = cursor.lastrowid
            
            botMsg = """Для пополнения баланса аккаунта воспользуйтесь данной [ссылкой](https://qiwi.com/payment/form/99999?extra%5B%27accountType%27%5D=nickname&extra%5B%27account%27%5D=TURSO912&currency=643&blocked[0]=accountType&blocked[1]=account&blocked[2]=currency) или кнопкой 'Пополнить баланс'

**Для пополнения укажите в комментарии:** `{}`

Для проверки баланса воспользуйтесь пунктом меню 'Аккаунт' или нажмите 'Проверить баланс'""".format(payid)
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text='Проверить баланс', callback_data='CheckBalance'))
            kb.add(types.InlineKeyboardButton(text='Пополнить баланс', url="https://qiwi.com/payment/form/99999?extra%5B%27accountType%27%5D=nickname&extra%5B%27account%27%5D=TURSO912&currency=643&blocked[0]=accountType&blocked[1]=account&blocked[2]=currency"))
            bot.send_message(message.from_user.id, botMsg, reply_markup=kb, parse_mode='MarkdownV2')
            
            sqlite_connection.commit()
            sqlite_connection.close()
        except:
            bot.send_message(message.from_user.id, "Что-то пошло не так, попробуйте заново", reply_markup=keyboard)
            
    else:
        bot.send_message(message.from_user.id, text="Используйте меню", reply_markup=keyboard)

    
    

    print("id:" + str(message.from_user.id) + "\nmessage:" + str(message.text) + "\n")


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == "CheckBalance":
        # ПРОВЕРКА ПЛАТЕЖА
        bot.edit_message_text("Ваш баланс: {:.2f}".format(getBalance(call.message.chat.id)), call.message.chat.id, call.message.id)   
    elif int(call.data) > 0:
        try:
            sqlite_connection = sqlite3.connect('bot.db')
            cursor = sqlite_connection.cursor()
            cursor.execute("SELECT Price FROM products WHERE id=?", (int(call.data), ))
            price = cursor.fetchall()
            if len(price) > 0:
                price = price[0][0]
                if getBalance(call.message.chat.id) >= price:
                    cursor.execute("INSERT INTO costs (product, sum, id_user, status) VALUES (?, ?, ?, 'OK')", (int(call.data), price, call.message.chat.id))
                    sqlite_connection.commit()
                    getBalance(call.message.chat.id)

                    cursor.execute("SELECT Name, Product FROM products WHERE id=?", (int(call.data), ))
                    product = cursor.fetchall()
                    msg = "Ваш товар:\n" + product[0][0] + "\n" + product[0][1]
                    bot.send_message(call.message.chat.id, text=msg)

                else:
                    bot.send_message(call.message.chat.id, text="На счете недостаточно средств")

            else:
                bot.send_message(call.message.chat.id, text="Этого товара нет в наличии")
        except:
            pass


def QiwiCheck():
    qw = pyqiwi.Wallet("af02de4e7fd66cf6c5d47a0712f2debd", "+79509237110")
    counter = 0
    while True:
        
        try:
            sqlite_connection = sqlite3.connect('bot.db')
            cursor = sqlite_connection.cursor()
            counter = counter + 1
            print(counter)
            history = qw.history(rows=50, operation="IN")
            
            for i in history["transactions"]:
                if i.comment != None and i.sum.currency == 643 and i.status == "SUCCESS":
                    cursor.execute("UPDATE payments SET sum=?, status='OK' WHERE id=?", (i.sum.amount, i.comment))
                    try:
                        cursor.execute("INSERT INTO qiwi (id_tr, dati, status, sum, val, comment) VALUES (?, ?, ?, ?, ?, ?)", (i.txn_id, i.date, i.status, i.sum.amount, i.sum.currency, i.comment))
                        
                    except:
                        continue
            
            
            sqlite_connection.commit()
            
            time.sleep(1)
        except Exception as err:
            print(err)
            time.sleep(300)
            pass
def getBalance(id):
    try:
        sqlite_connection = sqlite3.connect('bot.db')
        cursor = sqlite_connection.cursor()
            
        cursor.execute("SELECT SUM(sum) FROM payments WHERE id_client=? AND status='OK'", (id, ))
        balance = cursor.fetchall()[0][0]
        if balance == None:
            balance = 0

        cursor.execute("SELECT SUM(sum) FROM costs WHERE id_user=? AND status='OK'", (id, ))
        costs = cursor.fetchall()[0][0]
        if costs != None:
            balance = balance - costs
        cursor.execute("UPDATE users SET moneys=? WHERE id_client=?", (balance, id))
        sqlite_connection.commit()

        return float(balance) 
    except Exception as err:
        print(err)
        return None

def StartBot():
    bot.polling(none_stop=True)


thread1 = Thread(target=QiwiCheck)
thread2 = Thread(target=StartBot)

thread1.start()
thread2.start()
thread1.join()
thread2.join()