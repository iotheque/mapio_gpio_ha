#!/usr/bin/python
# -*- coding:utf-8
import datetime
import logging
from pathlib import Path
from typing import Any

import gpiod  # type: ignore
from ha_mqtt.ha_device import HaDevice
from ha_mqtt.mqtt_device_base import MqttDeviceSettings
from ha_mqtt.mqtt_switch import MqttSwitch
from paho.mqtt.client import Client

# Pin definition
RELAY1_CTRL_PIN = 25

# callbacks for the on and off actions
def on(entity: MqttSwitch, name: str, gpio_ctrl: Any):
    logger = logging.getLogger(__name__)
    logger.info(f"ON command for {name}")
    if name == "RELAY1":
        gpio_ctrl.set_value(1)
        # report back as switched on
        entity.set_on()
    else:
        logger.error(f"Unknown device {name}")


def off(entity: MqttSwitch, name: str, gpio_ctrl: Any):
    logger = logging.getLogger(__name__)
    logger.info(f"OFF command for {name}")
    if name == "RELAY1":
        gpio_ctrl.set_value(0)
        # report back as switched off
        entity.set_off()
    else:
        logger.error(f"Unknown device {name}")


class MAPIO_GPIO:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        # RRELAY1_CTRL configuration
        chip = gpiod.chip(0)
        config = gpiod.line_request()
        config.request_type = gpiod.line_request.DIRECTION_OUTPUT
        self.relay1_ctrl = chip.get_line(RELAY1_CTRL_PIN)
        self.relay1_ctrl.request(config)

    def expose_mapio_gpio_to_ha(self):
        # instantiate an paho mqtt client and connect to the mqtt server
        self.client = Client("mapio-gpio-ha")
        self.client.connect("localhost", 1883)
        self.client.loop_start()

        # create device info dictionary
        dev = HaDevice("MapioGPIO", "mapio-gpio-769251")

        # instantiate an MQTTSwitch object for each GPIO
        self.relay1 = MqttSwitch(
            MqttDeviceSettings("RELAY1", "RELAY1", self.client, dev)
        )

        # assign callbacks actions
        self.relay1.callback_on = lambda: on(self.relay1, "RELAY1", self.relay1_ctrl)
        self.relay1.callback_off = lambda: off(self.relay1, "RELAY1", self.relay1_ctrl)

    def close_mapio_gpio_to_ha(self):
        # close the device for cleanup. Gets marked as offline/unavailable in homeassistant
        self.relay1_ctrl.set_value(0)
        self.relay1_ctrl.release()

        self.relay1.close()
        self.client.loop_stop()
        self.client.disconnect()
