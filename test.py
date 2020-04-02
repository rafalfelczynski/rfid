#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import menu
import server

mymenu = menu.Menu(server.Server(), "gate 1A")
try:
    mymenu.start()
except KeyboardInterrupt:
    print("keyboard")
    pass