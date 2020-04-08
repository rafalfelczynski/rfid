#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os


def runServer():
    os.system("gnome-terminal -- './runServer.py'")
    pass


def runClients():
    os.system("gnome-terminal -- ./runClient.py \"gate 1A\" =")
    os.system("gnome-terminal -- ./runClient.py \"gate 2B\" -")
    pass


def main():
    runServer()
    runClients()


if __name__ == '__main__':
    main()

