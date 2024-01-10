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
    elif name == "LED_R":
        with open("/sys/class/leds/LED2_R/brightness", "w") as brightness:
            brightness.write("1")
        entity.set_on()  # type: ignore
    elif name == "LED_G":
        with open("/sys/class/leds/LED2_G/brightness", "w") as brightness:
            brightness.write("1")
        entity.set_on()  # type: ignore
    elif name == "LED_B":
        with open("/sys/class/leds/LED2_B/brightness", "w") as brightness:
            brightness.write("1")
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
    elif name == "LED_R":
        with open("/sys/class/leds/LED2_R/brightness", "w") as brightness:
            brightness.write("0")
        entity.set_off()  # type: ignore
    elif name == "LED_G":
        with open("/sys/class/leds/LED2_G/brightness", "w") as brightness:
            brightness.write("0")
        entity.set_off()  # type: ignore
    elif name == "LED_B":
        with open("/sys/class/leds/LED2_B/brightness", "w") as brightness:
            brightness.write("0")
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

        # User leds for HA
        self.led_r = MqttSwitch(MqttDeviceSettings("LED_R", "LED_R", self.client, dev))
        self.led_r.callback_on = lambda: on(self.led_r, "LED_R", self.led_r)
        self.led_r.callback_off = lambda: off(self.led_r, "LED_R", self.led_r)

        self.led_g = MqttSwitch(MqttDeviceSettings("LED_G", "LED_G", self.client, dev))
        self.led_g.callback_on = lambda: on(self.led_g, "LED_G", self.led_g)
        self.led_g.callback_off = lambda: off(self.led_g, "LED_G", self.led_g)

        self.led_b = MqttSwitch(MqttDeviceSettings("LED_B", "LED_B", self.client, dev))
        self.led_b.callback_on = lambda: on(self.led_b, "LED_B", self.led_b)
        self.led_b.callback_off = lambda: off(self.led_b, "LED_B", self.led_b)

        # instantiate an MQTTDevice object for ANA0 input
        self.ups = MqttSensor(
            MqttDeviceSettings("UPS Voltage", "ups", self.client),
            "%",
            HaDeviceClass.BATTERY,
            True,
        )

    def refresh_mapio_gpio_to_ha(self) -> None:
        # Get PMIC model
        model = os.popen("vcgencmd pmicrd 0 | awk '{print $3}'").read()  # nosec
        if model.strip() == "a0":
            # MAX LINEAR MXL7704
            # Read AIN0 value
            output = os.popen("vcgencmd pmicrd 0x1d | awk '{print $3}'").read()  # nosec
            int_value = 2 * int(output, 16) / 100
        else:
            # DA9090 PMIC
            # Read AIN0 value
            output = os.popen("vcgencmd pmicrd 0x13 | awk '{print $3}'").read()  # nosec
            int_value = 4 * int(output, 16) / 100
        percent = 0
        if int_value > 4:
            percent = 100
        elif int_value > 3.75:
            percent = 75
        elif int_value > 3.5:
            percent = 50
        elif int_value > 3.25:
            percent = 25

        output = output.replace("volt=", "")
        output = output.replace("V", "")

        self.ups.publish_state(percent)

    def close_mapio_gpio_to_ha(self) -> None:
        # close the device for cleanup. Gets marked as offline/unavailable in homeassistant
        self.relay1_ctrl.set_value(0)
        self.relay1_ctrl.release()

        self.relay1.close()  # type: ignore
        self.ups.close()  # type: ignore
        self.led_r.close()  # type: ignore
        self.led_g.close()  # type: ignore
        self.led_b.close()  # type: ignore
        self.client.loop_stop()
        self.client.disconnect()
