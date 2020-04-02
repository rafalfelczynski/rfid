import sqlite3
from datetime import datetime


class Server:

    def __init__(self, ):
        self.__dbname = "server_database.db"
        self.__createTables()
        pass

    def __createTables(self):
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS EMPLOYEES(PESEL INTEGER PRIMARY KEY AUTOINCREMENT,"
                       " NAME VARCHAR, SURNAME VARCHAR)")
        cursor.execute("CREATE TABLE IF NOT EXISTS TERMINALS(ID INTEGER PRIMARY KEY AUTOINCREMENT,"
                       " LOCALISATION VARCHAR)")
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
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        res = cursor.execute("SELECT * FROM EMPLOYEES WHERE PESEL = ?", (pesel,)).fetchone()
        cursor.close()
        connection.close()
        return res

    def getEmployees(self):
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

    def addTerminal(self, localisation):
        localisation = localisation.upper().strip()
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM TERMINALS WHERE LOCALISATION = ? ", (localisation,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO TERMINALS(LOCALISATION) VALUES(?)", (localisation,))
            connection.commit()
            cursor.close()
            connection.close()
            return True
        else:
            return False
        pass

    def removeTerminal(self, localisation):
        localisation = localisation.upper().strip()
        return self.__removeHelp("DELETE FROM TERMINALS WHERE LOCALISATION = ?", (localisation,))
        pass

    def getTerminals(self):
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
        return self.__removeHelp("DELETE FROM CARDS WHERE CARD_ID = ?", str(cardId))
    pass

    def removeCardAssignment(self, cardId):
        return self.__removeHelp("UPDATE CARDS SET EMPLOYEE_PESEL = ? WHERE CARD_ID = ?", (None, str(cardId)))
    pass

    def getCards(self):
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM CARDS")
        res = cursor.fetchall()
        cursor.close()
        connection.close()
        return res

    def getUnknownCards(self):
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
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        if self.getEmployee(pesel) is not None:
            empId = pesel
        else:
            empId = cursor.execute("SELECT 1 FROM EMPLOYEES_REMOVED WHERE PESEL = ?", (pesel,)).fetchone()
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
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        res = cursor.execute("SELECT * FROM CARDS WHERE CARD_ID = ?", (str(cardId),)).fetchone()
        return res
    pass

    def logCard(self, cardId, localisation):
        localisation = localisation.upper().strip()
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        res = self.getCard(cardId)
        timeStr = datetime.now().strftime("%y/%m/%d %H:%M:%S")
        termId = cursor.execute("SELECT ID FROM TERMINALS WHERE LOCALISATION = ?", (localisation,)).fetchone()
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
        connection = sqlite3.connect(self.__dbname)
        cursor = connection.cursor()
        cursor.execute(str, args)
        connection.commit()
        res = (cursor.rowcount > 0)
        cursor.close()
        connection.close()
        return res



pass
