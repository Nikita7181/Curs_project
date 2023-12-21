import datetime
import logging
import os
import time
import telebot
import config

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)  # Outputs debug messages to console.
bot = telebot.TeleBot(config.token, threaded=True)

files = []
clearfiles = []
tosend = []
tosendfull = []

### Функция проверки режима
def checkmode():
    try:
        mode_file = open("mode.txt", "r")
        modestring = mode_file.read()
        mode_file.close()
        if modestring == '1':
            return True
        else:
            return False

    except:
        return False

## Функция массовой пассылки фотографий
def sendall(filename):
    for username in config.users:
        try:
            f = open(filename, 'rb')
            bot.send_photo(username, f)
        except:
            print(
                str(datetime.datetime.now()) + ' ' + 'Ошибка отправки файла ' + filename + ' пользователю ' + username)

## Функция записи последнего обработтанного файла
def writeproc(filename):
    try:
        last_file = open("last.txt", "w")
        last_file.write(filename)
        last_file.close()
        return last_file.close()
    except:
        return False

## Функция чтения последнего обработанного файла
def readproc():
    try:
        last_file = open("last.txt", "r")
        lasstring = last_file.read()
        last_file.close()
        lastint = str(lasstring)
        return lastint
    except:
        return -1

## Читаем последний обработанный файл
processed = readproc()
if processed == -1:
    print(str(datetime.datetime.now()) + ' ' + 'Не Удалось прочитать последний обработанный файл. Выходим')
    quit(2)

## Читаем список файлов
files = os.listdir(config.motiondir)
files = filter(lambda x: x.endswith('.jpg'), files)

## Очищаем список от снапшотов и расширений, сортируем
for file in files:
    if ('snapshot' in file) or ('last' in file) or ('-' in file):
        pass
    else:
        clearfile = file[:-4]
        clearfiles.append(clearfile)
        clearfiles.sort()

## Выбираем список необработанных файлов
for file in clearfiles:
    if int(file) > int(processed):
        tosend.append(file)

### Если есть что отправлять:
if len(tosend) > 0:
    try:
        if writeproc(tosend[-1]) == False:
            print(str(datetime.datetime.now()) + ' ' + 'Ошибка записи последнего элемента. Выходим!')
            quit(2)
        else:
            print(str(datetime.datetime.now()) + ' ' + 'Последний элемент записан успешно')
        ### Отправляем только если успешно записали последний - иначе будет бесконечная отправка
        ## Сначала проверяем режим
        if checkmode():

            ## Потом формируем список фалов с полным именем
            for filename in tosend:
                fullname = config.motiondir + '/' + filename + '.jpg'
                tosendfull.append(fullname)
            ## Потом отправляем неторопливо
            for filename in tosendfull:
                sendall(filename)
                time.sleep(1)
        else:
            print(str(datetime.datetime.now()) + ' ' + 'Режим отправки выключен')
    except:
        print(str(datetime.datetime.now()) + ' ' + 'Ошибка отправки')
else:
    print(str(datetime.datetime.now()) + ' ' + 'Нечего отправлять')