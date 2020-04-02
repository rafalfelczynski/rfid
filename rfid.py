import time

import RPi.GPIO as GPIO

from config import *  # pylint: disable=unused-wildcard-import

import lib.rfid.MFRC522 as MFRC522
import signal


def rfidRead():
    MIFAREReader = MFRC522.MFRC522()
    print("Press the red or green button to exit this test.")
    while GPIO.input(buttonRed) and GPIO.input(buttonGreen):
        (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
        if status == MIFAREReader.MI_OK:
            (status, uid) = MIFAREReader.MFRC522_Anticoll()
            if status == MIFAREReader.MI_OK:
                num = 0
                for i in range(0, len(uid)):
                    num += uid[i] << (i*8)
                print(f"Card read UID: {uid} > {num}")
                time.sleep(0.5)
    print("RFID disabled")
    time.sleep(0.5)


def test():
    print("\nRFID test.")
    rfidRead()


if __name__ == "__main__":
    test()
    GPIO.cleanup()  # pylint: disable=no-member
