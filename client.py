from pynput.keyboard import Key, Listener, KeyCode
import paho.mqtt.client as mqtt
import threading
import time
import random
from collections import deque
from server import TOPIC

ACCEPTED_KEYS = [Key.end, KeyCode.from_char("-"), KeyCode.from_char("=")]


class Client(threading.Thread):

    def __init__(self, broker, terminal, char):  #####
        super().__init__()
        self.isRunning = False
        self.readCards = deque()
        self.keys = deque()
        self.broker = broker
        self.terminal = terminal
        self.listener = Listener(on_press=self.__on_press, on_release=self.__on_release)
        self.listener.setDaemon(True)
        self.client = mqtt.Client()
        self.char = char  ## char tylko na potrzeby braku raspberry pi
    pass

    def __readCard(self):
        """
        metoda odczytująca numer karty i dodająca do kolejki kart
        :return:
        """
        cardId = random.randint(0, 5)
        self.readCards.append(cardId)

    def __logCard(self):
        """
        Metoda obslugująca zczytywaną karte
        :return:
        """
        if len(self.readCards) > 0:
            cardId = self.readCards.popleft()
            self.sendCardIdToServer(cardId)
    pass

    def __processNextKey(self):
        """
        Metoda obsługująca kolejne nacisniecia przycisków
        :return:
        """
        if len(self.keys) > 0:
            key = self.keys.popleft()
            if key == Key.end:
                self.stop()
                quit(0)
            elif key == KeyCode.from_char(self.char):  ###############
                self.__readCard()
    pass

    def __on_press(self, key):
        if ACCEPTED_KEYS.__contains__(key):
            self.keys.append(key)
    pass

    def __on_release(self, key):
        return True
    pass

    def __connectToBroker(self):
        self.client.connect(self.broker)
    pass

    def __disconectFromBroker(self):
        self.client.disconnect(self.broker)

    def sendCardIdToServer(self, cardId):
        self.client.publish(TOPIC, str(cardId) + ";" + self.terminal)

    def __main(self):
        while self.isRunning:
            self.__processNextKey()
            self.__logCard()
            time.sleep(0.001)
        pass

    def start(self):
        print("Czytnik został aktywowany")
        self.__connectToBroker()
        self.isRunning = True
        super().start()
        if not self.listener.is_alive():
            self.listener.start()
        pass

    def stop(self):
        self.isRunning = False
        self.__disconectFromBroker()
        self.listener.stop()

    def run(self) -> None:
        self.__main()
        pass


pass

