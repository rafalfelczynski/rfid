#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import server
import dbserver

broker = "rafal-MS-7B38"
port = 8883


def main():
    dbServ = dbserver.DBServer()
    serv = server.Server(dbServ, broker, port)
    serv.start()


if __name__ == "__main__":
    main()
