

        
# импортируем необходимые библиотеки
from imutils.video import VideoStream  # захват кадров с камеры
import imagezmq
import argparse  # обработка аргумента командной строки, содержащего IP-адрес сервера
import socket    # получение имени хоста Raspberry Pi
import time      # для учета задержки камеры перед отправкой кадров
 
# создаем парсер аргументов и парсим
ap = argparse.ArgumentParser()
ap.add_argument("-s", "--server-ip", required=True,
	help="ip address of the server to which the client will connect")
args = vars(ap.parse_args())
 
# инициализируем объект ImageSender с адресом сокета сервера
sender = imagezmq.ImageSender(connect_to="tcp://{}:5555".format(
	args["server_ip"]))
# получим имя хоста, инициализируем видео поток, 
# дадим датчику камеры прогреться
rpiName = socket.gethostname()
#vs = VideoStream(usePiCamera=True).start()
vs = VideoStream(src=0).start()
time.sleep(2.0)  # задержка для начального разогрева камеры
 
while True:
	# прочитать кадр с камеры и отправить его на сервер
	frame = vs.read()
	sender.send_image(rpiName, frame)