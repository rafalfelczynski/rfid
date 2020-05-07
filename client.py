from pynput.keyboard import Key, Listener, KeyCode
import paho.mqtt.client as mqtt
import threading
import time
import random
from collections import deque
from server import TOPIC

ACCEPTED_KEYS = [Key.end, KeyCode.from_char("-"), KeyCode.from_char("=")]


class Client(threading.Thread):

    def __init__(self, broker, port, terminal, char):  #####
        """
        konstruktor klasy klient
        :param broker: broker mosquitto, do którego będą wysyłane komunikaty
        :param terminal: nazwa terminala, który obsługuje klient
        :param char: znak na klawiaturze do nacisniecia jako symulacja sczytania karty
        """
        super().__init__()
        self.__isRunning = False
        self.__readCards = deque()
        self.__keys = deque()
        self.__broker = broker
        self.__port = port
        self.__terminal = terminal
        self.__listener = Listener(on_press=self.__on_press, on_release=self.__on_release)
        self.__listener.setDaemon(True)
        self.__client = mqtt.Client()
        self.__char = char  ## char tylko na potrzeby braku raspberry pi
        self.__condition = threading.Event()
    pass

    def __readCard(self):
        """
        metoda odczytująca numer karty i dodająca do kolejki kart
        :return:
        """
        cardId = random.randint(0, 5)
        self.__readCards.append(cardId)

    def __logCard(self):
        """
        Metoda obslugująca zczytywaną karte
        :return:
        """
        if len(self.__readCards) > 0:
            cardId = self.__readCards.popleft()
            self.sendCardIdToServer(cardId)
    pass

    def __processNextKey(self):
        """
        Metoda obsługująca kolejne nacisniecia przycisków
        :return:
        """
        if len(self.__keys) > 0:
            key = self.__keys.popleft()
            if key == Key.end:
                self.stop()
                quit(0)
            elif key == KeyCode.from_char(self.__char):  ###############
                self.__readCard()
    pass

    def __on_press(self, key):
        """
        metoda listenera klawiatury wykonywana po wcisnieciu klawisza
        :param key: klawisz wcisniety
        :return:
        """
        if ACCEPTED_KEYS.__contains__(key):
            self.__keys.append(key)
    pass

    def __on_release(self, key):
        """
        metoda listenera wykonywana przy zwolnieniu klawisza
        :param key: klawisz
        :return:
        """
        return True
    pass

    def __connectToBroker(self):
        """
        metoda łącząca klienta z brokerem
        :return:
        """
        self.__client.tls_set("ca.crt")
        self.__client.on_connect = self.__on_connect
        self.__client.reconnect_delay_set(0.5, 0.5)
        self.__client.connect(self.__broker, self.__port)
        self.__client.loop_start()
    pass

    def __tryToConnectUser(self, login, password):
        self.__client.username_pw_set(username=login, password=password)

    def __on_connect(self, client, userdata, flags, rc):
        self.__condition.set()

    def __disconectFromBroker(self):
        """
        metoda kończąca połączenie z brokerem
        :return:
        """
        self.__client.disconnect(self.__broker)

    def sendCardIdToServer(self, cardId):
        """
        metoda wysyłająca numer karty do brokera
        :param cardId: nr sczytanej karty
        :return:
        """
        self.__client.publish(TOPIC, str(cardId) + ";" + self.__terminal)

    def __main(self):
        """
        główna metoda klienta, pętla obsługująca wcisniete klawisze oraz sczytane karty
        :return:
        """
        while self.__isRunning:
            self.__processNextKey()
            self.__logCard()
            time.sleep(0.001)
        pass

    def start(self):
        """
        metoda do rozpoczęcia pracy klienta. Startuje nowy wątek
        :return:
        """
        self.__connectToBroker()
        while not self.__client.is_connected():
            login = input("Podaj login...")
            password = input("Podaj hasło...")
            self.__condition.clear()
            self.__tryToConnectUser(login, password)
            self.__condition.wait()
            if not self.__client.is_connected():
                print("Błędny login lub hasło")
        if self.__client.is_connected():
            self.__isRunning = True
            super().start()
            if not self.__listener.is_alive():
                self.__listener.start()
            print("Czytnik został aktywowany")
            pass
        else:
            print("Błąd brokera. Sprawdz czy serwis jest włączony")
        pass

    def stop(self):
        """
        metoda kończąca prace klienta
        :return:
        """
        self.__isRunning = False
        self.__disconectFromBroker()
        self.__listener.stop()

    def run(self) -> None:
        """
        metoda którą wykonuje wystartowany wątek
        :return:
        """
        self.__main()
        pass


pass

