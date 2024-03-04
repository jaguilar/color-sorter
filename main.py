#! /usr/bin/env pybricks-micropython

from pybricks.tools import wait
from pybricks.ev3devices import Motor, TouchSensor, ColorSensor
from pybricks.hubs import EV3Brick
from pybricks.parameters import Port, Stop, Button, Color, Direction
import micropython
from micropython import const

brick = EV3Brick()
left_touch = TouchSensor(Port.S1)
color_sensor = ColorSensor(Port.S3)
track_motor = Motor(Port.D)
chute_motor = Motor(Port.A)


def calibrate_track():
    calib_speed = const(250)
    track_motor.run(-calib_speed)

    while True:
        wait(5)
        if left_touch.pressed():
            track_motor.stop()
            track_motor.reset_angle(0)
            break

    max_angle = track_motor.run_until_stalled(calib_speed, Stop.COAST, 25)
    track_motor.run_target(
        360, max_angle // 5, Stop.BRAKE
    )  # We go almost all the way to the left to speed startup next time.
    return max_angle


def run_track_to_target(target_angle: int):
    track_motor.run_target(150, target_angle, Stop.BRAKE, wait=True)


class ChutePos:
    UP = None
    DOWN = None


def calibrate_chute():
    ChutePos.UP = chute_motor.run_until_stalled(-45, Stop.COAST, 45)
    ChutePos.DOWN = ChutePos.UP + 180


def chute_move(p: ChutePos, wait: bool = True):
    chute_motor.run_target(540, p, Stop.BRAKE, wait=wait)


def jiggle_track():
    start_angle = track_motor.angle()
    duty = 75
    for _ in range(15):
        track_motor.dc(duty)
        duty = -duty
        wait(150)
    track_motor.stop()
    track_motor.run_target(360, start_angle)


def chute_dump1():
    chute_move(ChutePos.DOWN, wait=False)
    # Jiggle the track slightly to get the piece to move down.
    jiggle_track()
    chute_move(ChutePos.UP)


def read_colors():
    # Scan the input colors.
    colors = []

    brick_colors = [Color.RED, Color.BLUE, Color.GREEN, Color.YELLOW]
    max_colors = const(7)

    while len(colors) < max_colors and not Button.CENTER in brick.buttons.pressed():
        color = color_sensor.color()
        if color in brick_colors:
            colors.append(color)
            brick.speaker.beep()
            wait(1500)
        else:
            wait(200)
    return colors


if __name__ == "__main__":
    max_angle = calibrate_track()
    calibrate_chute()
    chute_move(ChutePos.UP)
    colors = read_colors()
    wait(1000)  # Give some extra time to get the last brick ready.

    RED_ANGLE = 4 * max_angle // 5
    YELLOW_ANGLE = 3 * max_angle // 5
    GREEN_ANGLE = 2 * max_angle // 5
    BLUE_ANGLE = 1 * max_angle // 5

    i = 0
    micropython.heap_lock()

    while i < len(colors):
        color = colors[i]
        i += 1
        if color == Color.RED:
            run_track_to_target(RED_ANGLE)
        elif color == Color.YELLOW:
            run_track_to_target(YELLOW_ANGLE)
        elif color == Color.GREEN:
            run_track_to_target(GREEN_ANGLE)
        else:
            run_track_to_target(BLUE_ANGLE)

        chute_dump1()
