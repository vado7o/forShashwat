import asyncio
import datetime
import uuid
from collections.abc import MutableMapping
from urllib.parse import urlencode
import pyrebase
import telebot
from yookassa import Configuration, Payment
import config
import costs
import keyboards
import strings
from energies import energies
# import requests
# import flask
# from flask import Flask, request, Response

Configuration.configure(config.shop_id, config.shop_api_token)  # yookassa tokens

firebase = pyrebase.initialize_app(config.configs)
database = firebase.database()
storage = firebase.storage()

bot = telebot.TeleBot(config.token)

# app = Flask(__name__)
#
# @app.route('/', methods = ['POST', 'GET'])
# def index():
#     if request.headers.get('Sign') != None:
#         print(request.stream.read())
#     elif request.headers.get('content-type')=='application/json':
#         update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
#         bot.process_new_updates([update])
#         return  ''
#     else:
#         flask.abort(403)
#     if request.method == 'POST':
#         return Response('ok', status=200)
#     else:
#         return  " "
#
# if __name__ == "__main__":
#     from waitress import  serve
#     serve(app, host="0.0.0.0", port=8080)

@bot.message_handler(commands=['start'])
def welcome(message):
    name_id = str(message.from_user.username) + "_" + str(message.from_user.id)
    id = str(message.from_user.id)
    try:
        database.child('users').child(name_id).child('user_info').update({'info': str(message)})
        database.child('obnovleniya').update({id: False})
        saveData(name_id, 'enter')
        resetAll(id)
    except Exception as e:
        write_exceptions(e, name_id)
    deletePreMsg(name_id, message, id)
    msg = bot.send_message(message.chat.id, 'Выберите пункт меню:', reply_markup=keyboards.inlinekeyboard)
    createPreMsg(name_id, msg, id)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    name_id = str(call.from_user.username) + "_" + str(call.from_user.id)
    id = str(call.from_user.id)
    try:
        if database.child('obnovleniya').child(id).get().val() == True:
            bot.send_message(call.message.chat.id,
                             '️❗️❗️❗️Появилось обновление бота! Пожалуйста нажмите внизу кнопку \'/start\' чтобы обновить 👇👇👇',
                             reply_markup=keyboards.markup)
        else:
            # ЕСЛИ ПОЛЬЗОВАТЕЛЬ НАЖИМАЕТ РАССЧИТАТЬ ЭНЕРГИИ
            if call.data == "calc_energy":
                deletePreMsg(name_id, call.message, id)
                resetAll(id)
                bot.send_message(call.message.chat.id, 'Если нужно вернуться в меню - нажмите 👇',
                                 reply_markup=keyboards.inlinekeyboard4)
                sendTextBeforeCalc(name_id, id)

            # ПОЛЬЗОВАТЕЛЬ ИМЕЕТ НЕГАТИВ В ПЕРВОЙ ЭНЕРГИИ
            if call.data == "_haveNegativeFirst_":
                deletePreMsg(name_id, call.message, id)
                msg = bot.send_message(call.message.chat.id, strings.afterFirst, parse_mode='MarkdownV2', reply_markup=keyboards.inlinekeyboard18)
                createPreMsg(name_id, msg, id)

            # РАССЧЁТ ВТОРОЙ ЭНЕРГИИ
            if call.data == "second_energy":
                deletePreMsg(name_id, call.message, id)
                dateMonth = database.child(id).child("temp_month").get().val()
                database.child(id).update({"energy_b": int(dateMonth)})
                bot.send_message(call.message.chat.id, strings.secondEnergy.format(dateMonth=dateMonth), parse_mode='MarkdownV2')
                bot.send_message(call.message.chat.id, energies.get(int(dateMonth)))
                msg = bot.send_message(call.message.chat.id, '*Имеются ли в Вашей жизни негативные проявления из описания второй энергии 👆?*',
                                       parse_mode='MarkdownV2', reply_markup=keyboards.inlinekeyboard19)
                createPreMsg(name_id, msg, id)

            # ПОЛЬЗОВАТЕЛЬ ИМЕЕТ НЕГАТИВ ВО ВТОРОЙ ЭНЕРГИИ
            if call.data == "_haveNegativeSecond_":
                deletePreMsg(name_id, call.message, id)
                msg = bot.send_message(call.message.chat.id, strings.afterSecond, parse_mode='MarkdownV2',
                                           reply_markup=keyboards.inlinekeyboard14)
                createPreMsg(name_id, msg, id)

            # РАССЧЁТ ТРЕТЬЕЙ ЭНЕРГИИ
            if call.data == "third_energy":
                deletePreMsg(name_id, call.message, id)
                database.child(id).update({"temp_month": ""})
                dateYear = database.child(id).child("temp_year").get().val()
                bot.send_message(call.message.chat.id, strings.thirdEnergy.format(dateYear=dateYear), parse_mode='MarkdownV2')
                # Вычисляем сумму цифр года рождения
                i = 0
                temp_year = 0
                while i < len(dateYear):
                    temp_year += int(dateYear[i])
                    i += 1
                while temp_year > 22:
                    str_year = str(temp_year)
                    i = 0
                    temp_year = 0
                    while i < len(str_year):
                        temp_year += int(str_year[i])
                        i += 1
                database.child(id).update({"energy_c": temp_year})
                bot.send_message(call.message.chat.id, energies.get(temp_year))
                msg = bot.send_message(call.message.chat.id, '...', reply_markup=keyboards.inlinekeyboard15)
                createPreMsg(name_id, msg, id)

            # РАССЧЁТ ЧЕТВЁРТОЙ ЭНЕРГИИ
            if call.data == "fourth_energy":
                deletePreMsg(name_id, call.message, id)
                database.child(id).update({"temp_year": ""})
                en_a = database.child(id).child("energy_a").get().val()
                en_b = database.child(id).child("energy_b").get().val()
                en_c = database.child(id).child("energy_c").get().val()
                bot.send_message(call.message.chat.id, strings.fourthEnergy, parse_mode='MarkdownV2')
                # Вычисляем сумм цифр четвёртой энергии (если она изначально > 22)
                temp_enD = en_a + en_b + en_c
                while temp_enD > 22:
                    i = 0
                    str_enD = str(temp_enD)
                    temp_enD = 0
                    while i < len(str_enD):
                        temp_enD += int(str_enD[i])
                        i += 1
                resetAll(id)
                bot.send_message(call.message.chat.id, energies.get(temp_enD))
                msg = bot.send_message(call.message.chat.id, '...', reply_markup=keyboards.inlinekeyboard16)
                createPreMsg(name_id, msg, id)

            # ИТОГ РАССЧЁТОВ
            if call.data == "_conclusion_":
                deletePreMsg(name_id, call.message, id)
                msg = bot.send_message(call.message.chat.id, strings.conclusion, parse_mode='MarkdownV2', reply_markup=keyboards.inlinekeyboard17)
                createPreMsg(name_id, msg, id)

            # ЕСЛИ ВЫБРАНА КНОПКА ИНТЕНСИВ В ГЛАВНОМ МЕНЮ
            if call.data == "new_course":
                if database.child('restricted').child(id).get().val() == True:
                    deletePreMsg(name_id, call.message, id)
                    msg = bot.send_message(call.message.chat.id, '❌ Вы уже провели оплату ранее', reply_markup=keyboards.inlinekeyboard4)
                    createPreMsg(name_id, msg, id)
                else:
                    resetAll(id)
                    deletePreMsg(name_id, call.message, id)
                    msg = bot.send_message(call.message.chat.id, "*Выберите удобный для Вас способ оплаты:*", parse_mode='MarkdownV2',
                                       reply_markup=keyboards.inlinekeyboard12)
                    createPreMsg(name_id, msg, id)
                    saveData(name_id, 'new_course')

            # НАЖАТИЕ КНОПКИ "ВЕРНУТЬСЯ В ГЛАВНОЕ МЕНЮ"
            if call.data == "mainmenu":
                resetAll(id)
                deletePreMsg(name_id, call.message, id)
                msg = bot.send_message(call.message.chat.id, 'Выберите пункт меню:', reply_markup=keyboards.inlinekeyboard)
                createPreMsg(name_id, msg, id)

            # ВЫБРАНА ОПЛАТА БАНКОВСКОЙ КАРТОЙ
            if call.data == "bank_card":
                bot.send_message(call.message.chat.id, 'Если нужно вернуться в меню - нажмите 👇',
                                     reply_markup=keyboards.inlinekeyboard4)
                deletePreMsg(name_id, call.message, id)
                resetAll(id)
                saveData(name_id, 'bankCard')
                if database.child('restricted').child(id).get().val() == True:
                    msg = bot.send_message(call.message.chat.id, '❌ Вы уже провели оплату ранее',
                                           reply_markup=keyboards.inlinekeyboard4)
                    createPreMsg(name_id, msg, id)
                else:
                    bot.send_message(call.message.chat.id, '*ПЕРЕЙДИТЕ ПО ССЫЛКЕ НИЖЕ ДЛЯ ОПЛАТЫ: 👇👇👇*', parse_mode='MarkdownV2')
                    msg = bot.send_message(call.message.chat.id, '[*__🔗 ССЫЛКА ДЛЯ ОПЛАТЫ \- нажмите чтобы перейти к оплате__*]({url})'.format(url=generate_payment_link(call.message)),
                         parse_mode='MarkdownV2')
                    createPreMsg(name_id, msg, id)

            # ВЫБРАНА ОПЛАТА ПО SberPay
            if call.data == "sber_pay":
                saveData(name_id, 'sberPay')
                deletePreMsg(name_id, call.message, id)
                if database.child('restricted').child(id).get().val() == True:
                    msg = bot.send_message(call.message.chat.id, '❌ Вы уже провели оплату ранее', reply_markup=keyboards.inlinekeyboard4)
                    createPreMsg(name_id, msg, id)
                else:
                    resetAll(id)
                    bot.send_message(call.message.chat.id, 'Если нужно вернуться в меню - нажмите 👇', reply_markup=keyboards.inlinekeyboard4)
                    msg = bot.send_message(call.message.chat.id,
                                           "*📧 Пожалуйста напишите корректно Ваш email для получения чека после оплаты:*",
                                           parse_mode='MarkdownV2')
                    createPreMsg(name_id, msg, id)
                    bot.register_next_step_handler(msg, registerTextForMail)

            # ПОДТВЕРЖДЕНИЕ ПОЛЬЗОВАТЕЛЕМ ПРАВИЛЬНОСТИ ВВЕДЁННОГО ЕМАЙЛ
            if call.data == "verifyMail":
                deletePreMsg(name_id, call.message, id)
                database.child(id).update({"temp_email":call.message.text})
                saveData(name_id, 'verifyMail')
                if database.child('restricted').child(id).get().val() == True:
                    msg = bot.send_message(call.message.chat.id, '❌ Вы уже провели оплату ранее', reply_markup=keyboards.inlinekeyboard4)
                    createPreMsg(name_id, msg, id)
                else:
                    buy_process(call.message)

            # ОБО МНЕ
            if call.data == 'about':
                deletePreMsg(name_id, call.message, id)
                msg = bot.send_photo(call.message.chat.id, photo=open('elenaAbout.jpg', 'rb'), caption=strings.about, parse_mode='MarkdownV2', reply_markup=keyboards.inlinekeyboard2)
                createPreMsg(name_id, msg, id)
                saveData(name_id, 'about')

            # СОЦИАЛЬНЫЕ СЕТИ
            if call.data == 'socnet':
                deletePreMsg(name_id, call.message, id)
                msg = bot.send_message(call.message.chat.id, strings.socnet, parse_mode='MarkdownV2',
                                 reply_markup=keyboards.inlinekeyboard4)
                createPreMsg(name_id, msg, id)
                saveData(name_id, 'socnet')

            # ОТЗЫВЫ
            if call.data == "feedback":
                deletePreMsg(name_id, call.message, id)
                msg = bot.send_message(call.message.chat.id, strings.feedback, parse_mode='MarkdownV2',
                                 reply_markup=keyboards.inlinekeyboard4)
                createPreMsg(name_id, msg, id)
                saveData(name_id, 'feedback')


            if call.data == "main menu":    # ЕСТЬ ДРУГОЙ mainmenu ЭТОТ МОЖНО УДАЛИТь ПОТОМ!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                bot.send_message(call.message.chat.id, 'Пожалуйста, чтобы Вы хотели узнать?',
                                 reply_markup=keyboards.inlinekeyboard)
                saveData(name_id, 'main_menu')


            if call.data == "methods":  # ХЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗ
                bot.send_message(call.message.chat.id, 'Перечень применяемых мною методов:',
                                 reply_markup=keyboards.inlinekeyboard3)
                saveData(name_id, 'methods')

            if call.data == "Reiki":    # ХЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗ
                bot.send_message(call.message.chat.id, strings.reiki, parse_mode='MarkdownV2',
                                 reply_markup=keyboards.inlinekeyboard3)
                saveData(name_id, 'reiki')

            if call.data == "costs":     # ХЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗ
                bot.send_message(call.message.chat.id,
                                 "*Выберите пакет услуг чтобы ознакомиться с его содержанием и узнать стоимость:*",
                                 parse_mode='MarkdownV2',
                                 reply_markup=keyboards.inlinekeyboard5)
                saveData(name_id, 'costs')

            if call.data == "costs_reiki":      # ХЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗ
                bot.send_message(call.message.chat.id, strings.costs_reiki, parse_mode='MarkdownV2',
                                 reply_markup=keyboards.inlinekeyboard6)
                saveData(name_id, 'costs_reiki')

            if call.data == "costs_enmatrix":      # ХЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗ
                bot.send_message(call.message.chat.id, strings.costs_enmatrix, parse_mode='MarkdownV2',
                                 reply_markup=keyboards.inlinekeyboard6)
                saveData(name_id, 'costs_enmatrix')

            if call.data == "costs_taro":       # ХЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗ
                bot.send_message(call.message.chat.id, strings.costs_taro, parse_mode='MarkdownV2',
                                 reply_markup=keyboards.inlinekeyboard6)
                saveData(name_id, 'costs_taro')

            if call.data == "costs_enprivate":     # ХЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗ
                bot.send_message(call.message.chat.id, strings.costs_enprivate, parse_mode='MarkdownV2',
                                 reply_markup=keyboards.inlinekeyboard6)
                saveData(name_id, 'costs_enprivate')

            if call.data == "costs_short_enprivate":     # ХЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗ
                bot.send_message(call.message.chat.id, strings.costs_short_enprivate, parse_mode='MarkdownV2',
                                 reply_markup=keyboards.inlinekeyboard6)
                saveData(name_id, 'costs_short_enprivate')

            if call.data == "costs_vip":       # ХЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗ
                bot.send_message(call.message.chat.id, strings.costs_vip, parse_mode='MarkdownV2',
                                 reply_markup=keyboards.inlinekeyboard6)
                saveData(name_id, 'costs_vip')

            if call.data == "intro":              # ХЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗ
                bot.send_message(call.message.chat.id, "*Прослушайте вводную информацию:*", parse_mode='MarkdownV2')
                bot.send_audio(call.message.chat.id, audio='https://firebasestorage.googleapis.com/v0/b/pypsybot-38943.appspot.com/o/newcourse%2F2.ogg?alt=media&token=5ec3c734-28b6-42d5-b861-1fa330ffae81')
                bot.send_audio(call.message.chat.id, audio='https://firebasestorage.googleapis.com/v0/b/pypsybot-38943.appspot.com/o/newcourse%2F3.ogg?alt=media&token=7839354f-b188-4fb5-9857-4f622189c2e2')
                bot.send_message(call.message.chat.id, '1️⃣ Скелет и структура энергоматрицы:')
                bot.send_photo(call.message.chat.id, photo='https://firebasestorage.googleapis.com/v0/b/pypsybot-38943.appspot.com/o/newcourse%2Fphoto_2023-02-05_11-45-29.jpg?alt=media&token=05e332e1-ac76-4d0d-87a1-8cc1b0283c30')
                bot.send_audio(call.message.chat.id, audio='https://firebasestorage.googleapis.com/v0/b/pypsybot-38943.appspot.com/o/newcourse%2F4.ogg?alt=media&token=d14f8fd3-6a3f-4a84-a317-648558e70e0a')
                bot.send_message(call.message.chat.id, '2️⃣ Значения 22 энергий ✨')
                bot.send_document(call.message.chat.id, document='https://firebasestorage.googleapis.com/v0/b/pypsybot-38943.appspot.com/o/newcourse%2F%D0%9C%D0%B5%D1%82%D0%BE%D0%B4%D0%B8%D1%87%D0%BA%D0%B0.pdf?alt=media&token=76968a98-83f7-49bc-b89b-cc8c020f8547')
                bot.send_message(call.message.chat.id, '2☑️Ваша Задача⬇️')
                bot.send_audio(call.message.chat.id, audio='https://firebasestorage.googleapis.com/v0/b/pypsybot-38943.appspot.com/o/newcourse%2Faudio_2023-02-05_11-58-23.ogg?alt=media&token=b9171af4-8f25-4c5a-a9d1-2cc15b2d639d')
                bot.send_message(call.message.chat.id, 'Выберите пункт меню:', reply_markup=keyboards.inlinekeyboard8)
                saveData(name_id, 'intro')

            if call.data == "buy":                                # ХЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗЗ
                saveData(name_id, 'buy')
                if database.child('restricted').child(id).get().val() == True:
                    bot.send_message(call.message.chat.id, '❌ Вы уже провели оплату ранее', reply_markup=keyboards.inlinekeyboard4)
                else:
                    msg = bot.send_message(call.message.chat.id, "*Пожалуйста напишите корректно Ваш email для получения чека после оплаты:*",
                                 parse_mode='MarkdownV2')
                    bot.register_next_step_handler(msg, registerTextForMail)


    except Exception as e:
        write_exceptions(e, name_id)


# ПОСЛЕ НАЖАТИЯ КНОПКИ ДЛЯ РАССЧЁТА ЭНЕРГИЙ ВЫДАЁМ СНАЧАЛА ОБЩЕЕ СООБЩЕНИЯ И НАЧИНАЕМ ЖДАТЬ ДАТУ РОЖДЕНИЯ ПОЛЬЗОВАТЕЛЯ
def sendTextBeforeCalc(name_id, id):
    try:
        msg = bot.send_message(id, strings.beforeCalc, parse_mode='MarkdownV2')
        createPreMsg(name_id, msg, id)
        bot.register_next_step_handler(msg, registerDateForCalc)

    except Exception as e:
        write_exceptions(e, name_id)

# ПОЛУЧАЕМ ТЕКСТ С ДАТОЙ РОЖДЕНИЯ ОТ ПОЛЬЗОВАТЕЛЯ И НАЧИНАЕМ РАБОТУ С НИМ
def registerDateForCalc(message):
    global temp_date
    name_id = str(message.from_user.username) + "_" + str(message.from_user.id)
    id = str(message.from_user.id)
    try:
        # ВЫРАБАТЫВАЕМ ИЗ ВВЕДЁННОГО ТЕКСТА ДАТУ
        dateString = message.text.replace(".", "/").replace("-", "/").replace("*", "/").replace(":", "/").replace(",","/")
        dateDay = dateString.split("/")[0]
        dateMonth = dateString.split("/")[1]
        dateYear = dateString.split("/")[2]
        if len(dateDay) == 1: dateDay = "0" + dateDay
        if len(dateMonth) == 1: dateMonth = "0" + dateMonth
        dateString = dateDay + "/" + dateMonth + "/" + dateYear

        #ПРОПИСЫВАЕМ В БАЗУ ДАННЫХ ПОЛУЧЕННЫЕ ЗНАЧЕНИЯ МЕСЯЦА И ГОДА ДЛЯ ИХ ДАЛЬНЕЙШЕГО ИСПОЛЬЗОВАНИЯ ИЗ ДРУГИХ ФУНКЦИЙ
        database.child(id).update({"temp_month": dateMonth})
        database.child(id).update({"temp_year": dateYear})

        # ПРОВЕРЯЕМ ВВЕДЁННУЮ ДАТУ НА ВАЛИДНОСТЬ
        format = "%d/%m/%Y"
        date = datetime.datetime.strptime(dateString, format)
        deletePreMsg(name_id, message, id)

        #НАЧИНАЕМ ВЫЧИСЛЕНИЕ ПЕРВОЙ ЭНЕРГИИ (ЭНЕРГИИ ДНЯ)
        temp_date = int(dateDay)
        if int(dateDay) > 22:
            temp_date = int(dateDay[0]) + int(dateDay[1])
        database.child(id).update({"energy_a": temp_date})
        bot.send_message(message.chat.id, strings.firstEnergy.format(dateDay=dateDay), parse_mode='MarkdownV2')
        bot.send_message(message.chat.id, energies.get(temp_date))
        msg = bot.send_message(message.chat.id, '*Имеются ли в Вашей жизни негативные проявления из описания первой энергии 👆?*',
                         parse_mode='MarkdownV2', reply_markup=keyboards.inlinekeyboard13)
        createPreMsg(name_id, msg, id)


    except Exception as e:
        deletePreMsg(name_id, message, id)
        msg = bot.send_message(message.chat.id, "*❌ Ошибка при введении даты\! Попробуйте снова*", parse_mode='MarkdownV2', reply_markup=keyboards.inlinekeyboard4)
        sendTextBeforeCalc(msg, id)


# ФУНКЦИЯ ПОЛУЧЕНИЯ ЕМАЙЛ ОТ ПОЛЬЗОВАТЕЛЯ ПРИ ВЫБОРЕ ОПЛАТЫ ЧЕРЕЗ ЮКАССУ
def registerTextForMail(message):
    name_id = str(message.from_user.username) + "_" + str(message.from_user.id)
    id = str(message.from_user.id)
    try:
        resetAll(id)
        deletePreMsg(name_id, message, id)
        database.child(id).update({"temp_email":message.text})
        bot.send_message(message.chat.id, "*Подтвердите введённый емайл: *", parse_mode='MarkdownV2')
        msg = bot.send_message(message.chat.id, message.text, reply_markup=keyboards.inlinekeyboard9)
        createPreMsg(name_id, msg, id)

    except Exception as e:
        write_exceptions(e, name_id)

# @bot.pre_checkout_query_handler(func=lambda query: True)
# def checkout(pre_checkout_query):
#     bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True, error_message="Что-то пошло не так. Попробуйте позже.")
#
#
# @bot.message_handler(content_types=['successful_payment'])
# def got_payment(message):
#     bot.send_message(message.chat.id, 'Платеж на сумму {amount} руб. совершён успешно!'.format(
#                                 amount=costs.value))
#     bot.send_message(message.chat.id, strings.link_toCourse, parse_mode='MarkdownV2')
#     database.child('oplatili').set({message.chat.id: str(datetime.datetime.now())})
#     database.child('restricted').update({message.chat.id: True})

# ФОРМИРОВАНИЕ ССЫЛКИ НА ОПЛАТУ ЧЕРЕЗ ЮКАССУ
def buy_process(message):
    name_id = str(message.from_user.username) + "_" + str(message.from_user.id)
    id = message.chat.id
    mail = database.child(id).child("temp_email").get().val()
    bot.send_message(message.chat.id, 'Если нужно вернуться в меню - нажмите 👇',
                     reply_markup=keyboards.inlinekeyboard4)
    deletePreMsg(name_id, message, id)
    try:
        payment = Payment.create({
            "amount": {
                "value": costs.value,
                "currency": "RUB"
            },
            "capture": True,
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/EnergyPsyBot"
            },
            "description": "Курс Энерготерапии",
            "receipt": {
                "customer": {
                    "email": mail
                },
                "items": [
                    {
                        "description": costs.description,
                        "quantity": "1",
                        "amount": {
                            "value": costs.value,
                            "currency": "RUB"
                        },
                        "vat_code": "1"
                    }
                ]
            }
        }, uuid.uuid4())

        bot.send_message(message.chat.id, strings.textConfirmation, parse_mode='MarkdownV2')
        msg = bot.send_message(message.chat.id, '[*__🔗 ССЫЛКА ДЛЯ ОПЛАТЫ \- нажмите чтобы перейти к оплате__*]({url})'.format(url=payment.confirmation.confirmation_url),
                         parse_mode='MarkdownV2')
        createPreMsg(name_id, msg, id)
        asyncio.run(check_payment(payment.id, message))

    except Exception as e:
        bot.send_message(message.chat.id, "*⛔️ Ошибка ввода емайл адреса ️*", parse_mode='MarkdownV2',
                         reply_markup=keyboards.inlinekeyboard11)
        write_exceptions(e, "скорее всего неправильно введён емайл, но это не точно")

# ОЖИДАНИЕ НУЖНОГО СТАТУСА ПЛАТЕЖА ЮКАССЫ
async def check_payment(payment_id, message):
    name_id = str(message.chat.username) + "_" + str(message.chat.id)
    id = str(message.chat.id)
    status = Payment.find_one(payment_id).status
    try:
        while status == 'pending':
            status = Payment.find_one(payment_id).status
            print(status)
            await asyncio.sleep(3)

        if status == 'succeeded':
            deletePreMsg(name_id, message, id)
            bot.send_message(message.chat.id, 'Если нужно вернуться в меню - нажмите 👇',
                             reply_markup=keyboards.inlinekeyboard4)
            msg = bot.send_message(message.chat.id, 'Платеж на сумму {amount} руб. совершён успешно!'.format(
                                amount=costs.value))
            createPreMsg(name_id, msg, id)
            bot.send_message(message.chat.id, strings.link_toCourse, parse_mode='MarkdownV2')
            database.child('oplatili').set({name_id: str(datetime.datetime.now())})
            database.child('restricted').update({id: True})
            return True

        if status == 'canceled':
            deletePreMsg(name_id, message, id)
            bot.send_message(message.chat.id, 'Если нужно вернуться в меню - нажмите 👇',
                             reply_markup=keyboards.inlinekeyboard4)
            cancel_party = Payment.find_one(payment_id).cancellation_details.party
            cancel_reason = Payment.find_one(payment_id).cancellation_details.reason
            if cancel_reason == 'expired_on_confirmation':
                msg = bot.send_message(message.chat.id, 'ПЛАТЁЖ ОТМЕНЁН по причине истечения срока действия ссылки',
                             reply_markup=keyboards.inlinekeyboard11)
                createPreMsg(name_id, msg, id)
                database.child('users').child(name_id).child('bad_payments').push({cancel_party: str(cancel_reason) + "__" + str(datetime.datetime.now())})
            else:
                write_exceptions(cancel_reason, name_id)
                msg = bot.send_message(message.chat.id, 'ПЛАТЁЖ ОТМЕНЁН стороной {party} по причине {reason}'.format(
                    party=cancel_party,reason=cancel_reason), reply_markup=keyboards.inlinekeyboard11)
                createPreMsg(name_id, msg, id)
                database.child('users').child(name_id).child('bad_payments').push({cancel_party: str(cancel_reason) + "__" + str(datetime.datetime.now())})
            return False

    except Exception as e:
        write_exceptions(e, name_id)



# ФОРМИРОВАНИЕ ПЛАТЁЖНОЙ ССЫЛКИ PRODAMUS
def generate_payment_link(message):
    id = str(message.chat.id)
    name_id = str(message.chat.username) + "_" + str(message.chat.id)
    # URL платежной формы
    linktoform = 'https://pudovaes.payform.ru/'

    # Секретный ключ. Можно найти на странице настроек,
    # в личном кабинете платежной формы
    secret_key = 'a9ea0788f228459c'

    data = {
        # хххх - номер заказ в системе интернет-магазина
        'order_id': id,

        # +7хххххххххх - мобильный телефон клиента
        'customer_phone': '',

        # ИМЯ@prodamus.ru - e-mail адрес клиента
        'customer_email': '',

        # перечень товаров заказа
        'products': [
            {
                # название товара - необходимо прописать название вашего товара
                # //          (обязательный параметр)
                'name': 'приобретение интенсива Елены Пудовой',

                # цена за единицу товара, 123 - значение, которое нужно прописать
                # (обязательный параметр)
                'price': '50',

                # количество товара, х - значение, которое нужно прописать
                # (обязательный параметр)
                'quantity': '1',

                #  Тип оплаты, с возможными значениями (при необходимости заменить):
                # 	1 - полная предварительная оплата до момента передачи предмета расчёта;
                # 	2 - частичная предварительная оплата до момента передачи
                #       предмета расчёта;
                # 	3 - аванс;
                # 	4 - полная оплата в момент передачи предмета расчёта;
                # 	5 - частичная оплата предмета расчёта в момент его передачи
                #       с последующей оплатой в кредит;
                # 	6 - передача предмета расчёта без его оплаты в момент
                #       его передачи с последующей оплатой в кредит;
                # 	7 - оплата предмета расчёта после его передачи с оплатой в кредит.
                #      (не обязательно, если не указано будет взято из настроек
                #      Магазина на стороне системы)
                'paymentMethod': 1,

                #  Тип оплачиваемой позиции, с возможными
                #      значениями (при необходимости заменить):
                # 	1 - товар;
                # 	2 - подакцизный товар;
                # 	3 - работа;
                # 	4 - услуга;
                # 	5 - ставка азартной игры;
                # 	6 - выигрыш азартной игры;
                # 	7 - лотерейный билет;
                # 	8 - выигрыш лотереи;
                # 	9 - предоставление РИД;
                # 	10 - платёж;
                # 	11 - агентское вознаграждение;
                # 	12 - составной предмет расчёта;
                # 	13 - иной предмет расчёта.
                #  (не обязательно, если не указано будет взято из настроек Магазина на стороне системы)
                'paymentObject': 4,
            },
        ],

        #  дополнительные данные
        'customer_extra': f'приобретение интенсива Елены Пудовой\n{name_id} date: {datetime.datetime.now()}',

        #  для интернет-магазинов доступно только действие "Оплата"
        'do': 'pay',

        #  url-адрес для возврата пользователя без оплаты
        #    (при необходимости прописать свой адрес)
        'urlReturn': 'https://t.me/EnergyPsyBot',

        # url-адрес для возврата пользователя при успешной оплате
        #    (при необходимости прописать свой адрес)
        'urlSuccess': 'https://t.me/+BqBTovGu',

        #  служебный url-адрес для уведомления интернет-магазина
        #            о поступлении оплаты по заказу
        #  	         пока реализован только для Advantshop,
        #            формат данных настроен под систему интернет-магазина
        #            (при необходимости прописать свой адрес)
        # 'urlNotification': 'https://github.com/vado7o/psybot',

        #  код системы интернет-магазина, запросить у поддержки,
        #      для самописных систем можно оставлять пустым полем
        #      (при необходимости прописать свой код)
        'sys': '',

        #  метод оплаты, выбранный клиентом
        #  	     если есть возможность выбора на стороне интернет-магазина,
        #  	     иначе клиент выбирает метод оплаты на стороне платежной формы
        #        варианты (при необходимости прописать значение):
        #  	AC - банковская карта
        #  	PC - Яндекс.Деньги
        #  	QW - Qiwi Wallet
        #  	WM - Webmoney
        #  	GP - платежный терминал
        # 'payment_method': 'AC',

        #  сумма скидки на заказ
        #  	     указывается только в том случае, если скидка
        #        не прменена к товарным позициям на стороне интернет-магазина
        #  	     алгоритм распределения скидки по товарам
        #        настраивается на стороне пейформы
        # 'discount_value': 0.00,

        #  тип плательщика, с возможными значениями:
        #      FROM_INDIVIDUAL - Физическое лицо
        #      FROM_LEGAL_ENTITY - Юридическое лицо
        #      FROM_FOREIGN_AGENCY - Иностранная организация
        #      (не обязательно. если форма работает в режиме самозанятого
        #       значение по умолчанию: FROM_INDIVIDUAL)
        'npd_income_type': 'FROM_INDIVIDUAL',

        #  инн плательщика (при необходимости прописат)
        #      (обязательно, если форма в режиме самозанятого
        #       и тип плательщика FROM_LEGAL_ENTITY)
        'npd_income_inn': 423006573960,

        #  название компании плательщика (при необходимости прописать название)
        #           (обязательно, если форма в режиме самозанятого
        #            и тип плательщика FROM_LEGAL_ENTITY или FROM_FOREIGN_AGENCY)
        # 'npd_income_company': 'Название компании плательщика',

        #  срок действия ссылки в формате: дд.мм.гггг чч:мм или гггг-мм-дд чч:мм
        #       при необходимости добавить дату
        #       (не обязательно, по умолчанию срок действия ссылки не ограничен)
        # 'link_expired': 'дд.мм.гггг чч:мм',


        #  текст который будет показан пользователю после совершения оплаты
        #    (не обязательно)
        'paid_content': 'Поздравляем! Теперь у Вас есть доступ на закрытый канал - https://t.me/+BqBTovGupn05MGQy \nЖелаем удачи!',

        # '_param_хххх': 'psybotid'
    }

    # подписываем с помощью кастомной функции sign (см ниже)
    data['signature'] = sign(data, secret_key)

    # компануем ссылку с помощью кастомной функции http_build_query (см ниже)
    link = linktoform + '?' + urlencode(http_build_query(data))

    return link


# ПОДПИСЬ ПЛАТЁЖНОЙ ССЫЛКИ ПРОДАМУС
def sign(data, secret_key):
    import hashlib
    import hmac
    import json

    # переводим все значения data в string c помощью кастомной функции deep_int_to_string (см ниже)
    deep_int_to_string(data)

    # переводим data в JSON, с сортировкой ключей в алфавитном порядке, без пробелов и экранируем бэкслеши
    data_json = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':')).replace("/", "\\/")

    # создаем подпись с помощью библиотеки hmac и возвращаем ее
    return hmac.new(secret_key.encode('utf8'), data_json.encode('utf8'), hashlib.sha256).hexdigest()


# СИСТЕМНАЯ ФУНКЦИЯ ПРОДАМУС
def deep_int_to_string(dictionary):
    for key, value in dictionary.items():
        if isinstance(value, MutableMapping):
            deep_int_to_string(value)
        elif isinstance(value, list) or isinstance(value, tuple):
            for k, v in enumerate(value):
                deep_int_to_string({str(k): v})
        else: dictionary[key] = str(value)


# СИСТЕМНАЯ ФУНКЦИЯ ПРОДАМУС
def http_build_query(dictionary, parent_key=False):
    items = []
    for key, value in dictionary.items():
        new_key = str(parent_key) + '[' + key + ']' if parent_key else key
        if isinstance(value, MutableMapping):
            items.extend(http_build_query(value, new_key).items())
        elif isinstance(value, list) or isinstance(value, tuple):
            for k, v in enumerate(value):
                items.extend(http_build_query({str(k): v}, new_key).items())
        else:
            items.append((new_key, value))
    return dict(items)


# ОТСЮДА НАЧИНАЮТСЯ СИСТЕМНЫЕ ФУНКЦИИ


def saveData(name_id, folder):
    try:
        database.child('users').child(name_id).child('buttons').child(folder).push(str(datetime.datetime.now()))
    except Exception as e:
        write_exceptions(e, name_id)


def write_exceptions(e, name_id):
    try:
        with open('errors.txt', 'a', encoding='utf-8') as file:
            file.write("\n" + name_id + ": " + str(e) + " (" + str(datetime.datetime.now()) + ")")
    except Exception as e:
        print("Не могу записать " + str(e) + " в файл errors.txt")


def createPreMsg(name_id, message, id):
    try:
        database.child('messages').child(id).update({'previous_msg': message.id})
    except Exception as e:
        write_exceptions(e, name_id)


def deletePreMsg(name_id, message, id):
    try:
        bot.delete_message(message.chat.id, database.child('messages').child(id).child('previous_msg').get().val())
        database.child('messages').child(id).child('previous_msg').remove()
    except Exception as e:
        write_exceptions(e, name_id)


def resetAll(id):
    database.child(id).update({"energy_a": ""})
    database.child(id).update({"energy_b": ""})
    database.child(id).update({"energy_c": ""})
    database.child(id).update({"temp_email": ""})
    database.child(id).update({"temp_month": ""})
    database.child(id).update({"temp_year": ""})


bot.polling(non_stop=True)
# if __name__ == '__main__':
#     app.run()