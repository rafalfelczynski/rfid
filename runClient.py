#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

import client
broker = "localhost"


def main():
    cli = client.Client(broker, sys.argv[1], sys.argv[2])
    cli.start()


if __name__ == "__main__":
    main()
