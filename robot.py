import sys
import time
import random
import math
import os
import threading


class Program():
    interpretation_started_timestamp = time.time() * 1000

    pi = 3.141592653589793
    gamepadpadButton1 = None
    x = None
    y = None

    def kolesa(self, ):
        if (bool(gamepad.isPadPressed(1))):
            # получаем значения с геймпада
            self.x = [gamepad.padX(1), gamepad.padY(1)][0]
            self.y = [gamepad.padX(1), gamepad.padY(1)][1]

            if (self.x != 0 and self.y == 0):
                # лево/право
                brick.motor("M1").setPower(self.x)
                brick.motor("M2").setPower(-self.x)
            elif (self.y != 0):
                # врепёд/назад
                brick.motor("M1").setPower(-self.y)
                brick.motor("M2").setPower(-self.y)

        else:
            brick.motor("M1").powerOff()
            brick.motor("M2").powerOff()

        script.wait(1)

        return

    def manipulyator(self, ):
        if (bool(gamepad.isPadPressed(2))):
            # получаем значения с геймпада
            self.x = [gamepad.padX(2), gamepad.padY(2)][0]
            self.y = [gamepad.padX(2), gamepad.padY(2)][1]

            if (self.x != 0):
                # зажать/расжать
                # запускаем парралельный поток, что бы всё время работал сервопривод
                brick.motor("S1").setPower(self.x)
                # threading.Thread(target=self.control_motor_S1, args=(self.x)).start()
            else:
                # вверх/вниз
                brick.motor("S2").setPower(-(self.y + self.lasty) - 90)

            # запоминаем прошлое положение
            self.lastx = self.x
            self.lasty = self.y

        else:
            brick.motor("S1").powerOff()
            brick.motor("S2").powerOff()

        script.wait(10)

        return

    def control_motor_S1(self, x):
        # Управляем сервоприводом
        brick.motor("S1").setPower(x)

    def execMain(self):
        # запускаем видео-трансляцию
        script.system(
            "/etc/init.d/mjpg-encoder-ov7670 start --jpeg-qual 80 --white-black false && /etc/init.d/mjpg-streamer-ov7670 start")
        self.x = 0
        self.y = 0
        self.flag = 1

        self.lastx = 0
        self.lasty = 0
        while not gamepad.isConnected():
            script.wait(10)

        while True:
            # выключение робота
            if (gamepad.buttonWasPressed(5)):
                os.system("halt")

            # отключаем сервопривод, отвечающий за зажатие
            if (gamepad.buttonWasPressed(3)):
                brick.motor("S1").powerOff()
            
            # отключаем сервопривод, отвечающий за зажатие
            if (gamepad.buttonWasPressed(4)):
                brick.motor("S2").powerOff()

            # получаем флаг для выбора режика
            # если кнопка 1 нажата - режим манипулятора
            if (gamepad.buttonWasPressed(1)):
                self.flag = 1
            else:
                self.flag = 0

            if (self.flag == 0):
                self.kolesa()
            else:
                self.lastx = 0
                self.lasty = 0
                self.manipulyator()

            script.wait(1)


def main():
    program = Program()
    program.execMain()


if __name__ == '__main__':
    main()

