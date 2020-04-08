import sqlite3
from datetime import datetime


class DBServer:

    def __init__(self):
        """
        Konstruktor obiektu. Tworzy bazę danych i tabele, jesli nie istnieją
        """
        self.__dbname = "server_database.db"
        self.__createTables()
        pass

    def __createTables(self):
        """
        Metoda tworząca tabele z pracownikami, terminalami, kartami i logami uzycia kart
        :return:
        """
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS EMPLOYEES(PESEL INTEGER PRIMARY KEY AUTOINCREMENT,"
                       " NAME VARCHAR, SURNAME VARCHAR)")
        cursor.execute("CREATE TABLE IF NOT EXISTS TERMINALS(ID INTEGER PRIMARY KEY AUTOINCREMENT,"
                       " NAME VARCHAR)")
        cursor.execute("CREATE TABLE IF NOT EXISTS LOGS(ID INTEGER PRIMARY KEY AUTOINCREMENT, TERMINAL_ID INTEGER,"
                       " EMPLOYEE_PESEL INTEGER, TIME DATE, FOREIGN KEY(TERMINAL_ID) REFERENCES TERMINALS(ID),"
                       " FOREIGN KEY(EMPLOYEE_PESEL) REFERENCES EMPLOYEES(PESEL))")
        cursor.execute("CREATE TABLE IF NOT EXISTS CARDS(CARD_ID VARCHAR PRIMARY KEY,"
                       " EMPLOYEE_PESEL INTEGER, FOREIGN KEY(EMPLOYEE_PESEL) REFERENCES EMPLOYEES(PESEL))")
        cursor.execute("CREATE TABLE IF NOT EXISTS UNKNOWN_CARDS(ID INTEGER PRIMARY KEY AUTOINCREMENT, CARD_ID VARCHAR,"
                       " TERMINAL_ID INTEGER, TIME DATE, FOREIGN KEY(CARD_ID) REFERENCES CARDS(CARD_ID),"
                       " FOREIGN KEY(TERMINAL_ID) REFERENCES TERMINALS(ID))")
        cursor.execute("CREATE TABLE IF NOT EXISTS EMPLOYEES_REMOVED(ID INTEGER PRIMARY KEY AUTOINCREMENT, EMPLOYEE_PESEL INTEGER, NAME VARCHAR, SURNAME VARCHAR)")
        connection.commit()
        cursor.close()
        connection.close()
        pass

    def getEmployee(self, pesel):
        """
        :param pesel: pesel pracownika
        :return: dane pracownika z bazy, jeśli istnieje lub None, jeśli nie
        """
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        res = cursor.execute("SELECT * FROM EMPLOYEES WHERE PESEL = ?", (pesel,)).fetchone()
        cursor.close()
        connection.close()
        return res

    def getEmployees(self):
        """
        :return: lista wszystkich pracowników
        """
        connection = sqlite3.connect(self.__dbname)
        stmt = "SELECT PESEL, NAME, SURNAME FROM EMPLOYEES"
        cursor = connection.cursor()
        cursor.execute(stmt)
        workers = cursor.fetchall()
        cursor.close()
        connection.close()
        return workers
    pass

    def addEmployee(self, pesel, name, surname):
        """
        Metoda dodająca pracownika do bazy
        :param pesel: pesel pracownika
        :param name: imie pracownika
        :param surname: nazwisko pracownika
        :return: True jesli dodano pracownika, False jeśli pracownik już istnieje w bazie
        """
        if self.getEmployee(pesel) is None:
            name = name.upper().strip()
            surname = surname.upper().strip()
            connection = sqlite3.connect(self.__dbname)
            cursor = connection.cursor()
            cursor.execute("INSERT INTO EMPLOYEES(PESEL, NAME, SURNAME) VALUES(?, ?, ?)", (pesel, name, surname))
            connection.commit()
            cursor.close()
            connection.close()
            return True
        else:
            return False
    pass

    def removeEmployee(self, pesel):
        """
        Metoda usuwająca pracownika z bazy danych
        :param pesel:
        :return: True jeśli udało się usunąć pracownika, False jeśli pracownik nie istnieje
        """
        cardIds = self.__getEmployeeCardIds(pesel)
        if cardIds is not None:
            for i in range(0, len(cardIds)):
                self.removeCardAssignment(cardIds[i][0])
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        empData = cursor.execute("SELECT NAME, SURNAME FROM EMPLOYEES WHERE PESEL = ?", (pesel,)).fetchone()
        if empData is not None:
            cursor.execute("INSERT INTO EMPLOYEES_REMOVED(EMPLOYEE_PESEL, NAME, SURNAME) VALUES(?, ?, ?)", (pesel, empData[0], empData[1]))
            connection.commit()
            cursor.close()
            connection.close()
            return self.__removeHelp("DELETE FROM EMPLOYEES WHERE PESEL = ?", (pesel,))
        else:
            return False
        pass

    def addTerminal(self, terminal):
        """
        Metoda dodająca nowy terminal do bazy
        :param terminal: lokalizacja (traktowana jako unikalna nazwa) terminala
        :return: True jesli dodano terminal, False jesli juz istnieje
        """
        terminal = terminal.upper().strip()
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM TERMINALS WHERE NAME = ? ", (terminal,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO TERMINALS(NAME) VALUES(?)", (terminal,))
            connection.commit()
            cursor.close()
            connection.close()
            return True
        else:
            return False
        pass

    def removeTerminal(self, terminal):
        """
        Metoda usuwająca terminal z bazy
        :param terminal: lokalizacja terminala (unikalna nazwa)
        :return: True jesli usunieto, False jesli nie nistnieje
        """
        terminal = terminal.upper().strip()
        return self.__removeHelp("DELETE FROM TERMINALS WHERE NAME = ?", (terminal,))
        pass

    def getTerminals(self):
        """
        Metoda do pobierania danych o wszystkich obecnych terminalach
        :return: lista danych terminali
        """
        connection = sqlite3.connect(self.__dbname)
        stmt = "SELECT * FROM TERMINALS"
        cursor = connection.cursor()
        cursor.execute(stmt)
        terminals = cursor.fetchall()
        cursor.close()
        connection.close()
        return terminals
    pass

    def assignCard(self, cardId, pesel):
        """
        Metoda do przypisania danej karty do pracownika
        :param cardId: nr karty
        :param pesel: pesel pracownika
        :return: 0 jeśli wszystko się udało, -1 jeśli karta jest już przypisana do tego pracownika,
            -2 jesli karta ma innego wlasciciela, -3 jesli karta nie istnieje, -4 jesli pracownik nie istnieje
        """
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        if self.getEmployee(pesel) is not None:  # jesli pracownik istnieje
            resp = cursor.execute("SELECT * FROM CARDS WHERE CARD_ID = ?", (str(cardId),)).fetchone()
            if resp is not None:  # jesli karta istnieje
                if resp[1] is None:  # jesli karta nie ma wlasciciela
                    cursor.execute("UPDATE CARDS SET EMPLOYEE_PESEL = ? WHERE CARD_ID = ?", (pesel, str(cardId)))
                    connection.commit()
                    cursor.close()
                    connection.close()
                    return 0
                elif resp[1] == pesel:
                    return -1  # card already assigned to this employee
                else:
                    return -2  # card belongs to another employee
            else:
                return -3  # card not exists
        else:
            return -4  # employee not exists
        pass

    def addCard(self, cardId):
        """
        Metoda dodająca do bazy nową karte bez przypisania pracownika
        :param cardId: numer karty
        :return: True jesli dodano kartę, False jesli karta juz istnieje
        """
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM CARDS WHERE CARD_ID = ?", (cardId,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO CARDS(CARD_ID, EMPLOYEE_PESEL) VALUES(?, ?)", (str(cardId), None))
            connection.commit()
            cursor.close()
            connection.close()
            return True
        else:
            return False

    def removeCard(self, cardId):
        """
        Metoda usuwająca karte z bazy
        :param cardId: nr karty
        :return: True jesli usunieto, False jestli karta nie istnieje
        """
        return self.__removeHelp("DELETE FROM CARDS WHERE CARD_ID = ?", str(cardId))
    pass

    def removeCardAssignment(self, cardId):
        """
        Metoda usuwająca przypisanie pracownika do karty
        :param cardId: nr karty
        :return: True jesli usunieto przypisanie, False jesli karta nie istnieje
        """
        return self.__removeHelp("UPDATE CARDS SET EMPLOYEE_PESEL = ? WHERE CARD_ID = ?", (None, str(cardId)))
    pass

    def getCards(self):
        """
        Metoda pobierająca z bazy dane o kartach
        :return: lista dostepnych kart
        """
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM CARDS")
        res = cursor.fetchall()
        cursor.close()
        connection.close()
        return res

    def getUnknownCards(self):
        """
        Metoda pobierająca z bazy dane o użyciu nieznanych systemowi kart
        :return: lista logów dotyczących kart, ktorych nie ma w systemie
        """
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        cursor.execute("SELECT CARD_ID, TERMINAL_ID, TIME FROM UNKNOWN_CARDS")
        logs = cursor.fetchall()
        cursor.close()
        connection.close()
        if len(logs) > 0:
            terms = self.getTerminals()
            map = dict()
            for i in range(0, len(terms)):
                map.update({terms[i][0]: terms[i][1]})
            for i in range(0, len(logs)):
                logs[i] = (logs[i][0], map.get(logs[i][1]), logs[i][2])
            return logs
        else:
            return None

    def __getEmployeeCardIds(self, pesel):
        """
        Metoda pobierająca z bazy karty należące do danego pracownika
        :param pesel: pesel pracownika
        :return: lista kart pracownika lub None, jesli nie posiada zadnych kart
        """
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        cardIds = cursor.execute("SELECT CARD_ID FROM CARDS WHERE EMPLOYEE_PESEL = ?", (pesel,)).fetchall()
        cursor.close()
        connection.close()
        if len(cardIds) > 0:
            return cardIds
        else:
            return None

    def generateReport(self, pesel):
        """
        Metoda pobierająca dane z bazy do raportu czasu pracy pracownika
        :param pesel: pesel pracownika
        :return: lista logów kart pracownika lub None, jesli pracownik nie istnieje lub logi są puste
        """
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        if self.getEmployee(pesel) is not None:
            empId = pesel
        else:
            empId = cursor.execute("SELECT 1 FROM EMPLOYEES_REMOVED WHERE EMPLOYEE_PESEL = ?", (pesel,)).fetchone()
        if empId is not None:
            cursor.execute("SELECT TERMINAL_ID, TIME FROM LOGS WHERE EMPLOYEE_PESEL = ?", (pesel,))
            logs = cursor.fetchall()
            cursor.close()
            connection.close()
            if len(logs) > 0:
                terms = self.getTerminals()
                map = dict()
                for i in range(0, len(terms)):
                    map.update({terms[i][0]: terms[i][1]})
                for i in range(0, len(logs)):
                    logs[i] = (map.get(logs[i][0]), logs[i][1])
                return logs
            else:
                return None
        else:
            return None
    pass

    def getCard(self, cardId):
        """
        Metoda sprawdzająca czy karta istnieje w systemie
        :param cardId:
        :return: id karty i nr pracownika lub none, jesli karta nie istnieje
        """
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        res = cursor.execute("SELECT * FROM CARDS WHERE CARD_ID = ?", (str(cardId),)).fetchone()
        return res
    pass

    def logCard(self, cardId, terminal):
        """
        metoda zapisująca czas użycia karty w terminalu i dane o karcie
        :param cardId: nr karty
        :param terminal: lokalizacja(nazwa) terminala
        :return: void
        """
        terminal = terminal.upper().strip()
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        res = self.getCard(cardId)
        timeStr = datetime.now().strftime("%y/%m/%d %H:%M:%S")
        termId = cursor.execute("SELECT ID FROM TERMINALS WHERE NAME = ?", (terminal,)).fetchone()
        if res is not None:  # jesli karta w ogole istnieje w systemie
            empId = cursor.execute("SELECT EMPLOYEE_PESEL FROM CARDS WHERE CARD_ID = ?", (str(cardId),)).fetchone()
            if empId is not None and termId is not None:  # jesli pracownik i terminal istnieje to dopisz, jak karta istnieje ale nie ma pracownika to nie wpisuj nic, bo nie ma sensu
                cursor.execute("INSERT INTO LOGS(TERMINAL_ID, EMPLOYEE_PESEL, TIME) VALUES(?, ?, ?)", (termId[0], empId[0], timeStr))
        else:
            if termId is not None:  # jesli karta nie istnieje w systemie a została użyta
                cursor.execute("INSERT INTO UNKNOWN_CARDS(CARD_ID, TERMINAL_ID, TIME) VALUES(?, ?, ?)", (str(cardId), termId[0], timeStr))
        connection.commit()
        cursor.close()
        connection.close()
    pass

    def __removeHelp(self, str, args):
        """
        metoda pomocnicza do usuwania danych z bazy
        :param str: SQL string
        :param args: argumenty klauzul SQL stringa
        :return: True jesli coś usunięto, False jeśli nie
        """
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        cursor.execute(str, args)
        connection.commit()
        res = (cursor.rowcount > 0)
        cursor.close()
        connection.close()
        return res



pass
