#!/usr/bin/python
# -*- coding:utf-8
import logging
import os
from typing import Any

import gpiod  # type: ignore
from ha_mqtt.ha_device import HaDevice
from ha_mqtt.mqtt_device_base import MqttDeviceSettings
from ha_mqtt.mqtt_sensor import MqttSensor
from ha_mqtt.mqtt_switch import MqttSwitch
from ha_mqtt.util import HaDeviceClass
from paho.mqtt.client import Client  # type: ignore

# Pin definition
RELAY1_CTRL_PIN = 25


# callbacks for the on and off actions
def on(entity: MqttSwitch, name: str, gpio_ctrl: Any) -> None:
    logger = logging.getLogger(__name__)
    logger.info(f"ON command for {name}")
    if name == "RELAY1":
        gpio_ctrl.set_value(1)
        # report back as switched on
        entity.set_on()  # type: ignore
    else:
        logger.error(f"Unknown device {name}")


def off(entity: MqttSwitch, name: str, gpio_ctrl: Any) -> None:
    logger = logging.getLogger(__name__)
    logger.info(f"OFF command for {name}")
    if name == "RELAY1":
        gpio_ctrl.set_value(0)
        # report back as switched off
        entity.set_off()  # type: ignore
    else:
        logger.error(f"Unknown device {name}")


class MAPIO_GPIO:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        # RELAY1_CTRL configuration
        chip = gpiod.chip(0)
        config = gpiod.line_request()
        config.request_type = gpiod.line_request.DIRECTION_OUTPUT
        self.relay1_ctrl = chip.get_line(RELAY1_CTRL_PIN)
        self.relay1_ctrl.request(config)

    def expose_mapio_gpio_to_ha(self) -> None:
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

        # instantiate an MQTTDevice object for ANA0 input
        self.ups = MqttSensor(
            MqttDeviceSettings("UPS Voltage", "ups", self.client),
            "V",
            HaDeviceClass.BATTERY,
            True,
        )

    def refresh_mapio_gpio_to_ha(self) -> None:
        # Read AIN0 value
        output = os.popen("vcgencmd pmicrd 1d | awk '{print $3}'").read()  # nosec
        int_value = 2 * int(output, 16) / 100
        output = output.replace("volt=", "")
        output = output.replace("V", "")
        self.ups.publish_state(int_value)

    def close_mapio_gpio_to_ha(self) -> None:
        # close the device for cleanup. Gets marked as offline/unavailable in homeassistant
        self.relay1_ctrl.set_value(0)
        self.relay1_ctrl.release()

        self.relay1.close()  # type: ignore
        self.client.loop_stop()
        self.client.disconnect()
