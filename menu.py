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
from server import Server
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


ACCEPTED_KEYS = [Key.up, Key.down, Key.esc, Key.right, KeyCode.from_char("k")]


class Menu:

    def __init__(self, _server, localisation):
        """
        konstruktor klasy
        :param _server: obiekt klasy Server
        :param localisation: lokaliacja terminala
        """
        self.curInd = 0
        self.enterClicked = False
        self.acceptKeyboard = True
        self.isRunning = False
        self._server = _server
        self.options = [("\t1. Dodaj pracownika", self.__addEmployee),
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
        self.listener = Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.setDaemon(True)
        self.keys = list()
        self.std = sys.stdin
        self.localisation = localisation
        self.lastCard = None

    pass

    def __printMenu(self):
        """
        Metoda wypisująca na ekranie menu aplikacji
        :return: void
        """
        optionsTemp = self.options.copy()
        optionsTemp[self.curInd] = ("==>" + optionsTemp[self.curInd][0], optionsTemp[self.curInd][1])
        print("Zmień opcje strzałkami góra/doł. Zatwierdź strzałką w prawo. Aby wyjśc wcisnij Esc")
        for i in range(0, len(optionsTemp)):
            print(optionsTemp[i][0])
    pass

    def start(self):
        """
        Metoda rozpoczynająca prace aplikacji
        :return:
        """
        self.isRunning = True
        if not (self.listener.is_alive()):
            self.listener.start()
        clear()
        self.__printMenu()
        self.main()

    def __menuUp(self):
        """
        Metoda przesuwająca wybór opcji o 1 w góre
        :return: void
        """
        if self.curInd == 0:
            self.curInd = len(self.options) - 1
        else:
            self.curInd -= 1
    pass

    def __menuDown(self):
        """
        Metoda przesuwająca wybór opcji o 1 w dol
        :return:
        """
        if self.curInd == len(self.options) - 1:
            self.curInd = 0
        else:
            self.curInd += 1

    pass

    def __choose(self):
        """
        Metoda wykonująca funkcje skorelowaną z wybraną przez użytkownika opcją
        :return:
        """
        self.listener.stop()
        self.acceptKeyboard = False
        function = self.options[self.curInd][1]
        clear()
        flushInput()
        function()
        self.__printMenu()
        self.acceptKeyboard = True
        self.listener = Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.setDaemon(True)
        if not (self.listener.is_alive()):
            self.listener.start()
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
        res = self._server.addEmployee(pesel, name, surname)
        if res:
            print(f"Dodano pracownika {name} {surname}")
        else:
            print("Błąd, nie dodano pracownika. Prawdopodobnie pracownik już istnieje")
    pass

    def __removeEmployee(self):
        """
        Metoda do usuwania użytkownika
        :return:
        """
        pesel = input("Podaj pesel pracownika... ")
        res = self._server.removeEmployee(pesel)
        if res:
            print(f"Usunięto pracownika")
        else:
            print("Błąd, nie usunięto pracownika. Prawdopodobnie pracownik nie istnieje")
    pass

    def __addTerminal(self):
        """
        Metoda do dodawania terminala
        :return:
        """
        localisation = input("Podaj lokalizację terminala... ")
        res = self._server.addTerminal(localisation)
        if res:
            print(f"Dodano terminal {localisation}")
        else:
            print(f"Błąd, nie dodano terminala {localisation}. Prawdopodobnie terminal już istnieje")
    pass

    def __removeTerminal(self):
        """
        Metoda do usuwania terminala
        :return:
        """
        localisation = input("Podaj lokalizację terminala... ")
        res = self._server.removeTerminal(localisation)
        if res:
            print(f"Usunięto terminal {localisation}")
        else:
            print(f"Błąd, nie usunięto terminala {localisation}. Prawdopodobnie terminal nie istnieje")
        pass

    def __waitPress(self, key, di):
        """
        Metoda chwilowego listenera klawiatury, który uaktywniany jest przy dodawaniu nowej karty lub przypisywaniu karty do pracownika.
        Metoda ta akceptuje tylko przycisk K i esc, wywoływana jest tylko raz
        :param key: klawisz wcisniety
        :param di: slownik ze zmienną typu bool, wskazująca czy wycofano się ze zczytywania karty
        :return: False - kończy prace listneera
        """
        if key == KeyCode.from_char("k"):
            return False  # stops listener
        if key == Key.esc:
            di.update({"quitted": True})
            return False
    pass

    def __waitForCard(self):
        """
        Metoda oczekująca na wcisniecie klawisza k, symulującego przylozenie karty do czytnika
        :return: numer zczytanej akrty lub None w przypadku rezygnacji
        """
        cardPresent = False
        di = {"quitted": False}
        listener = Listener(on_press=lambda key: self.__waitPress(key, di), on_release=None)
        listener.start()
        time.sleep(0.01)
        print("Przygotuj kartę i przyłóż do czytnika")
        while not cardPresent:
            if not listener.is_alive():  # hitting "k" on keyboard stops temporary listener
                cardPresent = True
            else:
                time.sleep(0.005)
            pass
        flushInput()
        if not di.get("quitted"):
            return random.randint(0, 5)
        else:
            print("Rezygnacja")
            return None
    pass

    def __readCard(self):
        """
        metoda przypisująca numer karty do ostatnio zczytanej karty
        :return:
        """
        self.lastCard = random.randint(0, 5)

    def __addCardWAss(self):
        """
        Metoda dodająca karte do systemu bez przypisywania jej do pracownika
        :return:
        """
        cardId = self.__waitForCard()
        if cardId is not None:
            res = self._server.addCard(cardId)
            if res:
                print(f"Dodano nową kartę o numerze {str(cardId)}")
            else:
                print(f"Karta o numerze {str(cardId)} już istnieje")
    pass

    def __removeCard(self):
        """
        metoda usuwająca karte z systemu
        :return:
        """
        cardId = self.__waitForCard()
        if cardId is not None:
            res = self._server.removeCard(cardId)
            if res:
                print("Usunięto kartę o numerze ", cardId)
            else:
                print("Brak w systemie karty o numerze ", cardId)

    def __assignCard(self):
        """
        Metoda do przypisania karty danemu pracownikowi
        :return:
        """
        flushInput()
        pesel = input("Podaj pesel pracownika... ")
        cardId = self.__waitForCard()
        if cardId is not None:
            res = self._server.assignCard(cardId, pesel)
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
                    res = self._server.addCard(cardId)
                    if res:
                        flushInput()
                        ans = input("\nKarta dodana, przypisać pracownika?[t/n]... ")
                        if ans.upper() == "T":
                            res = self._server.assignCard(cardId, pesel)
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
                    res = self._server.addEmployee(pesel, name, surname)
                    if res:
                        print("Pracownik dodany")
                    else:
                        print("Nieznany błąd")
                else:
                    print("\nRezygnacja")
    pass

    def __removeCardAssignment(self):
        """
        Metoda do usuwania przypisania karty do pracownika
        :return:
        """
        cardId = self.__waitForCard()
        if cardId is not None:
            res = self._server.removeCardAssignment(cardId)
            if res:
                print(f"Przypisanie karty o numerze {str(cardId)} zresetowane")
            else:
                print(f"Błąd, karta o numerze {str(cardId)} nie istnieje")
            pass

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
        return delta.total_seconds()/3600

    def __generateReport(self):
        """
        Metoda do generowania raportu pracy pracownika
        :return:
        """
        print("Generowanie raportu...")
        pesel = input("Podaj pesel pracownika... ")
        logs = self._server.generateReport(pesel)
        if logs is not None:
            empData = self._server.getEmployee(pesel)
            timeStr = datetime.now().strftime("%y.%m.%d godz. %H.%M.%S")
            fileName = "raport_prac_" + empData[1] + "_" + empData[2] + "_" + timeStr + ".csv"
            with open(fileName, "w+", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(("Terminal", "Czas wejścia", "Czas wyjścia", "Czas pracy"))
                for i in range(0, len(logs)):
                    if i+1 < len(logs):
                        writer.writerow((logs[i][0], logs[i][1], logs[i+1][1], "%.2f" % self.__dateSubs(logs[i+1][1], logs[i][1])))
                    else:
                        writer.writerow((logs[i][0], logs[i][1], "---", "---"))
            print("Raport wygenerowany do pliku: "+fileName)
        else:
            print("Brak raportu do wygenerowania")
    pass

    def __printEmployees(self):
        """
        Metoda wypisująca dostepnych pracowników
        :return:
        """
        li = self._server.getEmployees()
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
        li = self._server.getTerminals()
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
        li = self._server.getCards()
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
        logs = self._server.getUnknownCards()
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

    def on_press(self, key):
        """
        Metoda wykonywana przy nacisnieciu przycisku na klawiaturze
        :param key: przycisk wcisniety
        :return:
        """
        if self.acceptKeyboard:
            if ACCEPTED_KEYS.__contains__(key):
                self.keys.append(key)
    pass

    def on_release(self, key):
        """
        Metoda waykonywana przy zwalnianiu przycisniecia przycisku
        :param key: przycisk ktory byl wcisniety
        :return:
        """
        return True
    pass

    def main(self):
        """
        Główna metoda programu. BusyLoop. Obsługuje kolejne przycisniecia przycisku i logi kart
        :return:
        """
        while self.isRunning:
            try:
                self.processNextKey()
                time.sleep(0.001)
                self.__logCard()
            except Exception as ex:
                print(ex)
        pass
    pass

    def processNextKey(self):
        """
        Metoda obsługująca kolejne nacisniecia przycisków
        :return:
        """
        if len(self.keys) > 0:
            key = self.keys[0]
            if not self.enterClicked:
                if key == Key.up:
                    self.__menuUp()
                    clear()
                    self.__printMenu()
                elif key == Key.down:
                    self.__menuDown()
                    clear()
                    self.__printMenu()
                elif key == Key.esc:
                    self.isRunning = False
                    self.listener.stop()
                    quit(0)
                elif key == Key.right:
                    self.enterClicked = True
                    flushInput()
                    print("Opcja: "+self.options[self.curInd][0][1:] + "- Potwierdź, wciskając ponownie strzałkę w prawo")
                elif key == KeyCode.from_char("k"):
                    self.__readCard()
            else:
                if key == Key.right:
                    self.__choose()
                else:
                    flushInput()
                    clear()
                    print("\nRezygnacja")
                    self.__printMenu()
                self.enterClicked = False
            self.keys.pop(0)
    pass

    def __logCard(self):
        """
        Metoda obslugująca zczytywaną karte
        :return:
        """
        if self.lastCard is not None:
            print(self.lastCard)
            self._server.logCard(self.lastCard, self.localisation)
            self.lastCard = None
    pass


pass

