'''
file: manage_remote.py
author: Tawn Kramer
date: 2019-01-24
desc: Control a remote donkey robot over network
'''
import time
import math
import donkeycar as dk
from donkeycar.parts.camera import PiCamera
from donkeycar.parts.actuator import PCA9685, PWMSteering, PWMThrottle
from donkeycar.parts.network import MQTTValueSub, MQTTValuePub
from donkeycar.parts.image import ImgArrToJpg

cfg = dk.load_config()

V = dk.Vehicle()

print("starting up", cfg.DONKEY_UNIQUE_NAME, "for remote management.")


#CAMERA

if cfg.DONKEY_GYM:
    from donkeycar.parts.dgym import DonkeyGymEnv 
    cam = DonkeyGymEnv(cfg.DONKEY_SIM_PATH, env_name=cfg.DONKEY_GYM_ENV_NAME)
    threaded = True
    inputs = ["steering", 'throttle']
else:
    inputs = []
    cam = PiCamera(image_w=cfg.IMAGE_W, image_h=cfg.IMAGE_H, image_d=cfg.IMAGE_DEPTH)

V.add(cam, inputs=inputs, outputs=["camera/arr"], threaded=True)

img_to_jpg = ImgArrToJpg()
V.add(img_to_jpg, inputs=["camera/arr"], outputs=["camera/jpg"])

pub_cam = MQTTValuePub("donkey/%s/camera" % cfg.DONKEY_UNIQUE_NAME, broker=cfg.MQTT_BROKER)
V.add(pub_cam, inputs=["camera/jpg"])

#REALSENSE

if cfg.REALSENSE:

    from donkeycar.parts.realsense2 import RS_T265
    from donkeycar.parts.pid import PID

    sub_controls = MQTTValueSub("donkey/%s/controls" % cfg.DONKEY_UNIQUE_NAME, def_value=(0., 0.), broker=cfg.MQTT_BROKER)
    V.add(sub_controls, outputs=["steering", "target_speed"])

    rs = RS_T265()
    V.add(rs, outputs=["pos", "vel", "acc", "img"], inputs= ["target_speed"], threaded=True)

    pid = PID()
    V.add(pid, inputs=["vel", "pos", "acc", "target_speed"], outputs=["throttle", "state"])

    pub_state = MQTTValuePub("donkey/%s/state" % cfg.DONKEY_UNIQUE_NAME, broker=cfg.MQTT_BROKER)
    V.add(pub_state, inputs=["state"])

else:

    sub_controls = MQTTValueSub("donkey/%s/controls" % cfg.DONKEY_UNIQUE_NAME, def_value=(0., 0.), broker=cfg.MQTT_BROKER)
    V.add(sub_controls, outputs=["steering", "throttle"])


#STEERING 

if not cfg.DONKEY_GYM:

    steering_controller = PCA9685(cfg.STEERING_CHANNEL, cfg.PCA9685_I2C_ADDR, busnum=cfg.PCA9685_I2C_BUSNUM)
    steering = PWMSteering(controller=steering_controller,
                                    left_pulse=cfg.STEERING_LEFT_PWM, 
                                    right_pulse=cfg.STEERING_RIGHT_PWM)

    throttle_controller = PCA9685(cfg.THROTTLE_CHANNEL, cfg.PCA9685_I2C_ADDR, busnum=cfg.PCA9685_I2C_BUSNUM)
    throttle = PWMThrottle(controller=throttle_controller,
                                    max_pulse=cfg.THROTTLE_FORWARD_PWM,
                                    zero_pulse=cfg.THROTTLE_STOPPED_PWM, 
                                    min_pulse=cfg.THROTTLE_REVERSE_PWM)

    V.add(steering, inputs=['steering'])
    V.add(throttle, inputs=['throttle'])


V.start(rate_hz=cfg.DRIVE_LOOP_HZ)