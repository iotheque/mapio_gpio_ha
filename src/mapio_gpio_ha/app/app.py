"""Main app to control MAPIO GPIO HA."""

#!/usr/bin/python
import logging
import os
from pathlib import Path
from typing import Any

import gpiod
from ha_mqtt.ha_device import HaDevice
from ha_mqtt.mqtt_device_base import MqttDeviceBase, MqttDeviceSettings
from ha_mqtt.mqtt_sensor import MqttSensor
from ha_mqtt.mqtt_switch import MqttSwitch
from ha_mqtt.util import HaBinarySensorDeviceClass, HaSensorDeviceClass
from paho.mqtt.client import Client
from paho.mqtt.enums import CallbackAPIVersion

# Pin definition
RELAY1_CTRL_PIN = 25


class MqttTicSensor(MqttDeviceBase):
    """Create the MQTT TIC sensor.

    Args:
        MqttDeviceBase: herit from MqttDeviceBase
    """

    device_type = "sensor"

    def __init__(
        self,
        settings: MqttDeviceSettings,
        unit: str,
        device_class: HaSensorDeviceClass,
        state_class: str,
        send_only: bool = False,
    ):
        """Create sensor instance."""
        self.device_class = device_class
        self.unit_of_measurement = unit
        self.state_class = state_class
        super().__init__(settings, send_only)

    def pre_discovery(self) -> None:
        """Prediscovered function for MqttTicSensor."""
        self.add_config_option("device_class", self.device_class.value)  # type: ignore
        self.add_config_option("unit_of_measurement", self.unit_of_measurement)  # type: ignore
        self.add_config_option("state_class", self.state_class)  # type: ignore


class MqttBinarySensor(MqttDeviceBase):
    """class that implements an arbitrary binary sensor.

    :param unit_of_measurement: string containing the unit of measurement, example: '°C'
    :param device_class: :class:`~ha_mqtt.util.HaSensorDeviceClass` device class of this sensor
    :param settings: as in :class:`~ha_mqtt.mqtt_device_base.MqttDeviceBase`
    """

    device_type = "binary_sensor"

    def __init__(
        self,
        settings: MqttDeviceSettings,
        device_class: HaBinarySensorDeviceClass,
        send_only: bool = False,
    ):
        """Create sensor instance."""
        self.device_class = device_class
        super().__init__(settings, send_only)

    def pre_discovery(self) -> None:
        """Prediscovered function for MqttBinarySensor."""
        self.add_config_option("device_class", self.device_class.value)  # type: ignore


# callbacks for the on and off actions
def on(entity: MqttSwitch, name: str, gpio_ctrl: Any) -> None:
    """Callback called when a ON command is received.

    Args:
        entity (MqttSwitch): object that has been triggered
        name (str): Name of entity
        gpio_ctrl (Any): gpio control handler
    """
    logger = logging.getLogger(__name__)
    logger.info(f"ON command for {name}")
    if name == "RELAY1":
        gpio_ctrl.set_value(1)
        # report back as switched on
        entity.set_on()  # type: ignore
    elif name == "LED_R":
        with Path.open(Path("/sys/class/leds/LED2_R/brightness"), "w") as brightness:
            brightness.write("1")
        entity.set_on()  # type: ignore
    elif name == "LED_G":
        with Path.open(Path("/sys/class/leds/LED2_G/brightness"), "w") as brightness:
            brightness.write("1")
        entity.set_on()  # type: ignore
    elif name == "LED_B":
        with Path.open(Path("/sys/class/leds/LED2_B/brightness"), "w") as brightness:
            brightness.write("1")
        entity.set_on()  # type: ignore
    else:
        logger.error(f"Unknown device {name}")


def off(entity: MqttSwitch, name: str, gpio_ctrl: Any) -> None:
    """Callback called when a OFF command is received.

    Args:
        entity (MqttSwitch): object that has been triggered
        name (str): Name of entity
        gpio_ctrl (Any): gpio control handler
    """
    logger = logging.getLogger(__name__)
    logger.info(f"OFF command for {name}")
    if name == "RELAY1":
        gpio_ctrl.set_value(0)
        # report back as switched off
        entity.set_off()  # type: ignore
    elif name == "LED_R":
        with Path.open(Path("/sys/class/leds/LED2_R/brightness"), "w") as brightness:
            brightness.write("0")
        entity.set_off()  # type: ignore
    elif name == "LED_G":
        with Path.open(Path("/sys/class/leds/LED2_G/brightness"), "w") as brightness:
            brightness.write("0")
        entity.set_off()  # type: ignore
    elif name == "LED_B":
        with Path.open(Path("/sys/class/leds/LED2_B/brightness"), "w") as brightness:
            brightness.write("0")
        entity.set_off()  # type: ignore
    else:
        logger.error(f"Unknown device {name}")


class MAPIO_GPIO:
    """MAPIO GPIO object."""

    def __init__(self) -> None:
        """Initialise the MAPIO GPIO object."""
        self.logger = logging.getLogger(__name__)
        # RELAY1_CTRL configuration
        chip = gpiod.chip(0)
        config = gpiod.line_request()
        config.request_type = gpiod.line_request.DIRECTION_OUTPUT
        self.relay1_ctrl = chip.get_line(RELAY1_CTRL_PIN)
        self.relay1_ctrl.request(config)

    def expose_mapio_gpio_to_ha(self) -> None:
        """Expose the desired GPIO to HA."""
        # instantiate an paho mqtt client and connect to the mqtt server
        self.client = Client(CallbackAPIVersion.VERSION2, "mapio-gpio-ha")
        self.client.connect("localhost", 1883)
        self.client.loop_start()

        # create device info dictionary
        dev = HaDevice("MapioGPIO", "mapio-gpio-769251")

        # instantiate an MQTTSwitch object for each GPIO
        self.relay1 = MqttSwitch(MqttDeviceSettings("RELAY1", "RELAY1", self.client, dev))

        # assign callbacks actions
        self.relay1.callback_on = lambda: on(self.relay1, "RELAY1", self.relay1_ctrl)
        self.relay1.callback_off = lambda: off(self.relay1, "RELAY1", self.relay1_ctrl)
        self.relay1.start()

        # User leds for HA
        self.led_r = MqttSwitch(MqttDeviceSettings("LED_R", "LED_R", self.client, dev))
        self.led_r.callback_on = lambda: on(self.led_r, "LED_R", self.led_r)
        self.led_r.callback_off = lambda: off(self.led_r, "LED_R", self.led_r)
        self.led_r.start()

        self.led_g = MqttSwitch(MqttDeviceSettings("LED_G", "LED_G", self.client, dev))
        self.led_g.callback_on = lambda: on(self.led_g, "LED_G", self.led_g)
        self.led_g.callback_off = lambda: off(self.led_g, "LED_G", self.led_g)
        self.led_g.start()

        self.led_b = MqttSwitch(MqttDeviceSettings("LED_B", "LED_B", self.client, dev))
        self.led_b.callback_on = lambda: on(self.led_b, "LED_B", self.led_b)
        self.led_b.callback_off = lambda: off(self.led_b, "LED_B", self.led_b)
        self.led_b.start()

        # instantiate an MQTTDevice object for ANA0 input
        self.ups = MqttSensor(
            MqttDeviceSettings("UPS Voltage", "ups", self.client, dev),
            HaSensorDeviceClass.BATTERY,
            "%",
            True,
        )
        self.ups.start()

        self.on_charge = MqttBinarySensor(
            MqttDeviceSettings("Battery charging", "battery_charging", self.client, dev),
            HaBinarySensorDeviceClass.BATTERY_CHARGING,
            True,
        )
        self.on_charge.start()

    def refresh_mapio_gpio_to_ha(self) -> None:
        """Function that refresh values to send to HA."""
        # Get PMIC model
        model = os.popen("vcgencmd pmicrd 0 | awk '{print $3}'").read()  # noqa
        if model.strip() == "a0":
            # MAX LINEAR MXL7704
            # Read AIN0 value
            output = os.popen("vcgencmd pmicrd 0x1d | awk '{print $3}'").read()  # noqa
            int_value = 2 * int(output, 16) / 100
        else:
            # DA9090 PMIC
            # Read AIN0 value
            output = os.popen("vcgencmd pmicrd 0x13 | awk '{print $3}'").read()  # noqa
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

        self.ups.update_state(percent)

        # Check power is present
        chg_acok_n = os.popen("gpioget --numeric -c 2 9").read().strip()  # noqa
        if chg_acok_n == "0":
            self.on_charge.update_state("ON")
        else:
            self.on_charge.update_state("OFF")

    def close_mapio_gpio_to_ha(self) -> None:
        """Free the allocated resources."""
        # close the device for cleanup. Gets marked as offline/unavailable in homeassistant
        self.relay1_ctrl.set_value(0)
        self.relay1_ctrl.release()

        self.relay1.stop()  # type: ignore
        self.ups.stop()  # type: ignore
        self.on_charge.stop()  # type: ignore
        self.led_r.stop()  # type: ignore
        self.led_g.stop()  # type: ignore
        self.led_b.stop()  # type: ignore
        self.client.loop_stop()
        self.client.disconnect()
