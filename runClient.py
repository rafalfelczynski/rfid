#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

import client
broker = "rafal-MS-7B38"
port = 8883


def main():
    cli = client.Client(broker, port, sys.argv[1], sys.argv[2])
    cli.start()


if __name__ == "__main__":
    main()
