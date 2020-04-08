#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pynput.keyboard import Key, Listener, KeyCode
from os import system
import os
import time
import sys
import random
from termios import tcflush, TCIOFLUSH
import csv
from datetime import datetime
import paho.mqtt.client as mqtt
import serverlogs
from dbserver import DBServer
import threading


def clear():
    """
    Metoda czyszcząca okno terminala w którym działa aplikacja
    :return:
    """
    system('clear' if os.name == 'posix' else 'cls')
    sys.stdout.write('\033[2K\033[1G')
    pass


def flushInput():
    """
    metoda usuwająca wprowadzone przez użytkownika dane w terminalu
    :return:
    """
    sys.stdout.write('\033[2K\033[1G')
    tcflush(sys.stdin, TCIOFLUSH)
    pass


ACCEPTED_KEYS = [Key.up, Key.down, Key.esc, Key.right]
TOPIC = "cardId"


class Server:

    def __init__(self, dbserver, broker):
        """
        konstruktor klasy
        :param dbserver: obiekt klasy Server
        """
        self.__curInd = 0
        self.__enterClicked = False
        self.__acceptKeyboard = True
        self.__isRunning = False
        self.__dbserver = dbserver
        self.__options = [("\t1. Dodaj pracownika", self.__addEmployee),
                          ("\t2. Usuń pracownika", self.__removeEmployee),
                          ("\t3. Pokaż pracowników", self.__printEmployees),
                          ("\t4. Dodaj terminal RFID", self.__addTerminal),
                          ("\t5. Usuń terminal RFID", self.__removeTerminal),
                          ("\t6. Pokaż terminale", self.__printTerminals),
                          ("\t7. Dodaj kartę", self.__addCardWAss),
                          ("\t8. Usuń kartę", self.__removeCard),
                          ("\t9. Przypisz kartę do pracownika", self.__assignCard),
                          ("\t10. Pokaż karty", self.__printCards),
                          ("\t11. Usuń przypisanie karty do pracownika", self.__removeCardAssignment),
                          ("\t12. Generuj raport czasu pracy pracownika", self.__generateReport),
                          ("\t13. Generuj raport logowania nieznanych kart", self.__genRepUnkCards)]
        self.__listener = Listener(on_press=self.__on_press, on_release=self.__on_release)
        self.__listener.setDaemon(True)
        self.__keys = list()
        self.__client = mqtt.Client()
        self.__broker = broker
    pass

    def __printMenu(self):
        """
        Metoda wypisująca na ekranie menu aplikacji
        :return: void
        """
        optionsTemp = self.__options.copy()
        optionsTemp[self.__curInd] = ("==>" + optionsTemp[self.__curInd][0], optionsTemp[self.__curInd][1])
        print("Zmień opcje strzałkami góra/doł. Zatwierdź strzałką w prawo. Aby wyjśc wcisnij Esc")
        for i in range(0, len(optionsTemp)):
            print(optionsTemp[i][0])
    pass

    def start(self):
        """
        Metoda rozpoczynająca prace aplikacji
        :return:
        """
        self.__connectToBroker()
        self.__isRunning = True
        if not (self.__listener.is_alive()):
            self.__listener.start()
        clear()
        self.__printMenu()
        self.__main()
    pass

    def stop(self):
        self.__disconectFromBroker()
        self.__listener.stop()
        self.__isRunning = False

    def __connectToBroker(self):
        self.__client.connect(self.__broker)
        self.__client.on_message = self.__processMessage
        self.__client.subscribe(TOPIC)
        self.__client.loop_start()
    pass

    def __disconectFromBroker(self):
        self.__client.unsubscribe(TOPIC)
        self.__client.loop_stop()
        self.__client.disconnect(self.__broker)

    def __processMessage(self, client, userdata, message):
        # Decode message.
        message_decoded = (str(message.payload.decode("utf-8"))).split(";")
        # Print message to console.

        self.__dbserver.logCard(message_decoded[0], message_decoded[1])

    def __menuUp(self):
        """
        Metoda przesuwająca wybór opcji o 1 w góre
        :return: void
        """
        if self.__curInd == 0:
            self.__curInd = len(self.__options) - 1
        else:
            self.__curInd -= 1
    pass

    def __menuDown(self):
        """
        Metoda przesuwająca wybór opcji o 1 w dol
        :return:
        """
        if self.__curInd == len(self.__options) - 1:
            self.__curInd = 0
        else:
            self.__curInd += 1
    pass

    def __choose(self):
        """
        Metoda wykonująca funkcje skorelowaną z wybraną przez użytkownika opcją
        :return:
        """
        self.__listener.stop()
        self.__acceptKeyboard = False
        function = self.__options[self.__curInd][1]
        clear()
        flushInput()
        function()
        self.__printMenu()
        self.__acceptKeyboard = True
        self.__listener = Listener(on_press=self.__on_press, on_release=self.__on_release)
        self.__listener.setDaemon(True)
        if not (self.__listener.is_alive()):
            self.__listener.start()
        time.sleep(0.01)
    pass

    def __addEmployee(self):
        """
        Metoda do dodawania nowego użytkownika
        :return:
        """
        pesel = input("Podaj pesel pracownika... ")
        name = input("Podaj imię pracownika... ")
        surname = input("Podaj nazwisko pracownika... ")
        if pesel.isnumeric() and name.isalpha() and surname.isalpha():
            res = self.__dbserver.addEmployee(pesel, name, surname)
            if res:
                print(f"Dodano pracownika {name} {surname}")
            else:
                print("Błąd, nie dodano pracownika. Prawdopodobnie pracownik już istnieje")
        else:
            print("Błędne dane")
    pass

    def __removeEmployee(self):
        """
        Metoda do usuwania użytkownika
        :return:
        """
        pesel = input("Podaj pesel pracownika... ")
        if pesel.isnumeric():
            res = self.__dbserver.removeEmployee(pesel)
            if res:
                print(f"Usunięto pracownika")
            else:
                print("Błąd, nie usunięto pracownika. Prawdopodobnie pracownik nie istnieje")
        else:
            print("Błędny pesel")

    pass

    def __addTerminal(self):
        """
        Metoda do dodawania terminala
        :return:
        """
        terminal = input("Podaj nazwę terminala... ")
        res = self.__dbserver.addTerminal(terminal)
        if res:
            print(f"Dodano terminal {terminal}")
        else:
            print(f"Błąd, nie dodano terminala {terminal}. Prawdopodobnie terminal już istnieje")
    pass

    def __removeTerminal(self):
        """
        Metoda do usuwania terminala
        :return:
        """
        terminal = input("Podaj nazwę terminala... ")
        res = self.__dbserver.removeTerminal(terminal)
        if res:
            print(f"Usunięto terminal {terminal}")
        else:
            print(f"Błąd, nie usunięto terminala {terminal}. Prawdopodobnie terminal nie istnieje")
        pass

    def __addCardWAss(self):
        """
        Metoda dodająca karte do systemu bez przypisywania jej do pracownika
        :return:
        """
        cardId = input("Podaj numer karty... ")
        if cardId.isnumeric():
            res = self.__dbserver.addCard(cardId)
            if res:
                print(f"Dodano nową kartę o numerze {str(cardId)}")
            else:
                print(f"Karta o numerze {str(cardId)} już istnieje")
        else:
            print("Błąd w numerze karty")
    pass

    def __removeCard(self):
        """
        metoda usuwająca karte z systemu
        :return:
        """
        cardId = input("Podaj numer karty... ")
        if cardId.isnumeric():
            res = self.__dbserver.removeCard(cardId)
            if res:
                print("Usunięto kartę o numerze ", cardId)
            else:
                print("Brak w systemie karty o numerze ", cardId)
        else:
            print("Błąd w numerze karty")

    def __assignCard(self):
        """
        Metoda do przypisania karty danemu pracownikowi
        :return:
        """
        flushInput()
        pesel = input("Podaj pesel pracownika... ")
        cardId = input("Podaj numer karty... ")
        if cardId.isnumeric() and pesel.isnumeric():
            res = self.__dbserver.assignCard(cardId, pesel)
            if res == 0:
                print(f"Karta o numerze {str(cardId)} przypisana")
            elif res == -1:
                print("Karta jest już przypisana do tego pracownika")
            elif res == -2:
                print("Karta należy do innego pracownika"),
            elif res == -3:
                flushInput()
                ans = input(f"\nKarta o numerze {str(cardId)} nie istnieje, czy chcesz ją dodać?[t/n]... ")
                if ans.upper() == "T":
                    res = self.__dbserver.addCard(cardId)
                    if res:
                        flushInput()
                        ans = input("\nKarta dodana, przypisać pracownika?[t/n]... ")
                        if ans.upper() == "T":
                            res = self.__dbserver.assignCard(cardId, pesel)
                            if res == 0:
                                print("Karta przypisana")
                            else:
                                print("Niezidentyfikowany błąd")
                    else:
                        print("Wystąpił błąd. Sprawdź czy masz uprawienia do edycji plików")
            elif res == -4:
                flushInput()
                ans = input(f"\nPracownik o peselu {pesel} nie istnieje, czy chcesz go dodać?[t/n]... ")
                if ans.upper() == "T":
                    name = input("Podaj imię pracownika... ")
                    surname = input("Podaj nazwisko pracownika... ")
                    res = self.__dbserver.addEmployee(pesel, name, surname)
                    if res:
                        print("Pracownik dodany")
                    else:
                        print("Nieznany błąd")
                else:
                    print("\nRezygnacja")
        else:
            print("Błąd w numerze karty lub peselu")
    pass

    def __removeCardAssignment(self):
        """
        Metoda do usuwania przypisania karty do pracownika
        :return:
        """
        cardId = input("Podaj numer karty... ")
        if cardId.isnumeric():
            res = self.__dbserver.removeCardAssignment(cardId)
            if res:
                print(f"Przypisanie karty o numerze {str(cardId)} zresetowane")
            else:
                print(f"Błąd, karta o numerze {str(cardId)} nie istnieje")
            pass
        else:
            print("Błąd w numerze karty")

    def __dateSubs(self, dateStr1, dateStr2):
        """
        Metoda odejmująca od siebie 2 daty sformatowane w string o konkretnym formacie
        :param dateStr1: data1 - odjemna
        :param dateStr2: data2 - odjemnik
        :return: liczba godzin między dwiema datami
        """
        start = datetime.strptime(dateStr2, "%y/%m/%d %H:%M:%S")
        end = datetime.strptime(dateStr1, "%y/%m/%d %H:%M:%S")
        delta = end - start
        return delta  # .total_seconds()/3600

    def __generateReport(self):
        """
        Metoda do generowania raportu pracy pracownika
        :return:
        """
        print("Generowanie raportu...")
        pesel = input("Podaj pesel pracownika... ")
        if pesel.isnumeric():
            logs = self.__dbserver.generateReport(pesel)
            if logs is not None:
                empData = self.__dbserver.getEmployee(pesel)
                timeStr = datetime.now().strftime("%y.%m.%d godz. %H.%M.%S")
                fileName = "raport_prac_" + empData[1] + "_" + empData[2] + "_" + timeStr + ".csv"
                with open(fileName, "w+", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(("Terminal", "Czas wejścia", "Czas wyjścia", "Czas pracy"))
                    for i in range(0, len(logs), 2):
                        if i+1 < len(logs):
                            writer.writerow((logs[i][0], logs[i][1], logs[i+1][1], self.__dateSubs(logs[i+1][1], logs[i][1])))
                        else:
                            writer.writerow((logs[i][0], logs[i][1], "---", "---"))
                print("Raport wygenerowany do pliku: "+fileName)
            else:
                print("Brak raportu do wygenerowania")
        else:
            print("Błąd w peselu")
    pass

    def __printEmployees(self):
        """
        Metoda wypisująca dostepnych pracowników
        :return:
        """
        li = self.__dbserver.getEmployees()
        if len(li) != 0:
            for i in range(0, len(li)):
                print(li[i])
        else:
            print("Brak pracowników")
    pass

    def __printTerminals(self):
        """
        Metoda wypisująca dostępne terminale
        :return:
        """
        li = self.__dbserver.getTerminals()
        if len(li) != 0:
            for i in range(0, len(li)):
                print(li[i])
        else:
            print("Brak terminali")
    pass

    def __printCards(self):
        """
        Metoda wypisująca wszystkie dostępne w systemie karty
        :return:
        """
        li = self.__dbserver.getCards()
        if len(li) != 0:
            for i in range(0, len(li)):
                print(li[i])
        else:
            print("Brak kart")

    def __genRepUnkCards(self):
        """
        Metoda do generowania raportu użycia kart, których nie ma w systemie
        :return:
        """
        logs = self.__dbserver.getUnknownCards()
        if logs is not None:
            timeStr = datetime.now().strftime("%y.%m.%d godz. %H.%M.%S")
            fileName = "report_unknown_cards_" + timeStr + ".csv"
            with open(fileName, "w+", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(("ID karty", "Terminal", "Zarejestrowany czas"))
                for i in range(0, len(logs)):
                    writer.writerow((logs[i][0], logs[i][1], logs[i][2]))
            print("Raport wygenerowany do pliku: " + fileName)
        else:
            print("Brak raportu do wygenerowania")

    def __on_press(self, key):
        """
        Metoda wykonywana przy nacisnieciu przycisku na klawiaturze
        :param key: przycisk wcisniety
        :return:
        """
        if self.__acceptKeyboard:
            if ACCEPTED_KEYS.__contains__(key):
                self.__keys.append(key)
    pass

    def __on_release(self, key):
        """
        Metoda waykonywana przy zwalnianiu przycisniecia przycisku
        :param key: przycisk ktory byl wcisniety
        :return:
        """
        return True
    pass

    def __main(self):
        """
        Główna metoda programu. BusyLoop. Obsługuje kolejne przycisniecia przycisku i logi kart
        :return:
        """
        while self.__isRunning:
            try:
                self.__processNextKey()
                time.sleep(0.001)
            except Exception as ex:
                print(ex)
        pass
    pass

    def __processNextKey(self):
        """
        Metoda obsługująca kolejne nacisniecia przycisków
        :return:
        """
        if len(self.__keys) > 0:
            key = self.__keys[0]
            if not self.__enterClicked:
                if key == Key.up:
                    self.__menuUp()
                    clear()
                    self.__printMenu()
                elif key == Key.down:
                    self.__menuDown()
                    clear()
                    self.__printMenu()
                elif key == Key.esc:
                    self.stop()
                    quit(0)
                elif key == Key.right:
                    self.__enterClicked = True
                    flushInput()
                    print("Opcja: " + self.__options[self.__curInd][0][1:] + "- Potwierdź, wciskając ponownie strzałkę w prawo")
            else:
                if key == Key.right:
                    self.__choose()
                else:
                    flushInput()
                    clear()
                    self.__printMenu()
                    print("\nRezygnacja")
                self.__enterClicked = False
            self.__keys.pop(0)
    pass


pass

