# импортируем необходимые библиотеки
from imutils import build_montages   # монтаж всех входящих кадров
from datetime import datetime
import numpy as np
import imagezmq
import argparse
import imutils
import cv2
 
# создаем парсер аргументов и парсим их
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--prototxt", required=True,
	help="path to Caffe 'deploy' prototxt file")
ap.add_argument("-m", "--model", required=True,
	help="path to Caffe pre-trained model")
ap.add_argument("-c", "--confidence", type=float, default=0.2,
	help="minimum probability to filter weak detections")
ap.add_argument("-mW", "--montageW", required=True, type=int,
	help="montage frame width")
ap.add_argument("-mH", "--montageH", required=True, type=int,
	help="montage frame height")
args = vars(ap.parse_args())
imageHub = imagezmq.ImageHub()
 
# инициализируем список меток классов сети MobileNet SSD, обученной
# для детектирования, генерируем набор ограничивающих прямоугольников
# разного цвета для каждого класса
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
	"bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
	"dog", "horse", "motorbike", "person", "pottedplant", "sheep",
	"sofa", "train", "tvmonitor"]
 
# загружаем сериализованную модель Caffe с диска
print("[INFO] loading model...")
net = cv2.dnn.readNetFromCaffe(args["prototxt"], args["model"])
# инициализируем выбранный набор подсчитываемых меток классов,
# словарь-счетчик и словарь фреймов
 
# инициализируем словарь, который будет содержать информацию
# о том когда устройство было активным в последний раз
lastActive = {}
lastActiveCheck = datetime.now()
 
# храним ожидаемое число клиентов, период активности
# вычисляем длительность ожидания между проверкой
# на активность устройства

ESTIMATED_NUM_PIS = 4
ACTIVE_CHECK_PERIOD = 10
ACTIVE_CHECK_SECONDS = ESTIMATED_NUM_PIS * ACTIVE_CHECK_PERIOD
 
# назначаем ширину и высоту монтажного кадра
# чтобы просматривать потоки от всех клиентов вместе
mW = args["montageW"]
mH = args["montageH"]
# начинаем цикл по всем кадрам
while True:
	# получаем имя клиента и кадр,
	# подтверждаем получение
	dt = datetime.now()
	year = str(dt.year)
	month = str(dt.month)
	day = str(dt.day)
	hour = str(dt.hour)
	minute = str(dt.minute)
	second = str(dt.second)
	CONSIDER = set(["person", "car"])
	objCount = {obj: 0 for obj in CONSIDER}
	frameDict = {}
	
	(rpiName, frame) = imageHub.recv_image()
	imageHub.send_reply(b'OK')
 
	# если устройства нет в словаре lastActive,
	# это новое подключенное устройство
	if rpiName not in lastActive.keys():
		print("[INFO] receiving data from {}...".format(rpiName))
 
	# записываем время последней активности для устройства,
	# от которого мы получаем кадр
	lastActive[rpiName] = datetime.now()
	# изменяем размер кадра, чтобы ширина была не больше 400 пикселей,
	# захватываем размеры кадров и создаем блоб
	frame = imutils.resize(frame, width=400)
	(h, w) = frame.shape[:2]
	blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)),
		0.007843, (300, 300), 127.5)
 
	# передаем блоб нейросети, получаем предсказания
	net.setInput(blob)
	detections = net.forward()
 
	# сбрасываем число объектов для интересующего набора
	objCount = {obj: 0 for obj in CONSIDER}
	# циклически обходим детектированные объекты
	for i in np.arange(0, detections.shape[2]):
		# извлекаем вероятность соответствующего предсказания
		confidence = detections[0, 0, i, 2]
 
		# отфильтруем слабые предсказания,	
		# гарантируя минимальную достоверность
		if confidence > args["confidence"]:
			# извлекаем индекс метки класса
			idx = int(detections[0, 0, i, 1])
 
			# проверяем, что метка класса в множестве интересных нам
			if CLASSES[idx] in CONSIDER:
				# подсчитываем детектированный объект
				objCount[CLASSES[idx]] += 1
 
				# вычисляем координаты рамки, ограничивающей объект
				box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
				(startX, startY, endX, endY) = box.astype("int")
 
				# рисуем рамку вокруг объекта
				cv2.rectangle(frame, (startX, startY), (endX, endY),
					(255, 0, 0), 2)
				# отобразим имя клиента на кадре

	date =" " + year + "-" + month + "-" + day + " " + hour + ":" + minute + ":" + second
	cv2.putText(frame, rpiName + date, (10, 25),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
 
	# отобразим число объектов на кадре
	label = ", ".join("{}: {}".format(obj, count) for (obj, count) in
		objCount.items())
	cv2.putText(frame, label, (10, h - 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255,0), 2)
 
	# обновим кадр в словаре кадров клиентов
	frameDict[rpiName] = frame
 
	# построим общий кадр из словаря кадров
	montages = build_montages(frameDict.values(), (w, h), (mW, mH))
 
	# покажем смонтированный кадр на экране
	for (i, montage) in enumerate(montages):
		cv2.imshow("Home pet location monitor ({})".format(i),
			montage)
 
	# детектируем нажатие какой-либо клавиши
	key = cv2.waitKey(1) & 0xFF
	# если разница между текущим временем и временем последней активности 
	# больше порога, производим проверку
	if (datetime.now() - lastActiveCheck).seconds > ACTIVE_CHECK_SECONDS:
		# циклично обходим все ранее активные устройства
		for (rpiName, ts) in list(lastActive.items()):
			# удаляем клиент из словарей кадров и последних активных
			# если устройство неактивно
			if (datetime.now() - ts).seconds > ACTIVE_CHECK_SECONDS:
				print("[INFO] lost connection to {}".format(rpiName))
				lastActive.pop(rpiName)
				frameDict.pop(rpiName)
 
		# устанавливаем время последней активности
		lastActiveCheck = datetime.now()
 
	# если нажата клавиша `q`, выходим из цикла
	if key == ord("q"):
		break
 
# закрываем окна и освобождаем память
cv2.destroyAllWindows()
