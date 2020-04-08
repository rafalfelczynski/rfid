#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import server
import dbserver

broker = "localhost"


def main():
    dbServ = dbserver.DBServer()
    serv = server.Server(dbServ, broker)
    serv.start()

if __name__ == "__main__":
    main()
