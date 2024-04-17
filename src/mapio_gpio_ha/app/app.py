"""Main app to control MAPIO GPIO HA."""

#!/usr/bin/python
import logging
import os
from pathlib import Path
from typing import Any

import gpiod
import serial
from ha_mqtt.ha_device import HaDevice
from ha_mqtt.mqtt_device_base import MqttDeviceBase, MqttDeviceSettings
from ha_mqtt.mqtt_sensor import MqttSensor
from ha_mqtt.mqtt_switch import MqttSwitch
from ha_mqtt.util import HaDeviceClass
from paho.mqtt.client import Client

# Pin definition
RELAY1_CTRL_PIN = 25

# Exposed linky measures to HA
# "ACTIVE_REGISTER_TIER_DELIVERED"
HA_LINKY_MEASURES: list[dict[str, Any]] = [
    {
        "unit": "W",
        "device_class": HaDeviceClass.APPARENT_POWER,
        "state_class": "measurement",
        "exposed_variable": "apparent_power",
    },
    {
        "unit": "Wh",
        "device_class": HaDeviceClass.ENERGY,
        "state_class": "total_increasing",
        "exposed_variable": "current_summ_delivered",
    },
    {
        "unit": "Wh",
        "device_class": HaDeviceClass.ENERGY,
        "state_class": "total_increasing",
        "exposed_variable": "current_tier1_summ_delivered",
    },
    {
        "unit": "Wh",
        "device_class": HaDeviceClass.ENERGY,
        "state_class": "total_increasing",
        "exposed_variable": "current_tier2_summ_delivered",
    },
]

# /* 0x0000 */ 'currentSummDelivered',
# /* 0x0001 */ 'currentSummReceived',
# /* 0x0020 */ 'activeRegisterTierDelivered',
# /* 0x0100 */ 'currentTier1SummDelivered',
# /* 0x0102 */ 'currentTier2SummDelivered',
# /* 0x0104 */ 'currentTier3SummDelivered',
# /* 0x0106 */ 'currentTier4SummDelivered',
# /* 0x0108 */ 'currentTier5SummDelivered',
# /* 0x010A */ 'currentTier6SummDelivered',
# /* 0x010C */ 'currentTier7SummDelivered',
# /* 0x010E */ 'currentTier8SummDelivered',
# /* 0x0110 */ 'currentTier9SummDelivered',
# /* 0x0112 */ 'currentTier10SummDelivered',
# /* 0x0307 */ 'siteId',
# /* 0x0308 */ 'meterSerialNumber',
# Define the Linky read registers
LINKY_REGISTERS: list[dict[str, str]] = [
    {"name": "BASE", "exposed_variable": "current_summ_delivered"},
    {"name": "PAPP", "exposed_variable": "apparent_power"},
    {"name": "SINSTS", "exposed_variable": "apparent_power"},
    {"name": "SINSTS1", "exposed_variable": "apparent_power"},
    {"name": "HCHC", "exposed_variable": "current_tier1_summ_delivered"},
    {"name": "EASF01", "exposed_variable": "current_tier1_summ_delivered"},
    {"name": "EJPHN", "exposed_variable": "current_tier1_summ_delivered"},
    {"name": "BBRHCJB", "exposed_variable": "current_tier1_summ_delivered"},
    {"name": "HCHP", "exposed_variable": "current_tier2_summ_delivered"},
    {"name": "EASF02", "exposed_variable": "current_tier2_summ_delivered"},
    {"name": "EJPHPM", "exposed_variable": "current_tier2_summ_delivered"},
    {"name": "BBRHPJB", "exposed_variable": "current_tier2_summ_delivered"},
]


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
        device_class: HaDeviceClass,
        state_class: str,
        send_only: bool = False,
    ):
        """Create sensor instance."""
        self.device_class: Any = device_class
        self.unit_of_measurement = unit
        self.state_class = state_class
        super().__init__(settings, send_only)

    def pre_discovery(self) -> None:
        """Prediscovered function for MqttTicSensor."""
        self.add_config_option("device_class", self.device_class.value)
        self.add_config_option("unit_of_measurement", self.unit_of_measurement)
        self.add_config_option("state_class", self.state_class)


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

    def expose_mapio_gpio_to_ha(self, linky: bool = False) -> None:
        """Expose the desired GPIO to HA."""
        # instantiate an paho mqtt client and connect to the mqtt server
        self.client = Client("mapio-gpio-ha")
        self.client.connect("localhost", 1883)
        self.client.loop_start()
        self.linky_enable = linky

        # create device info dictionary
        dev = HaDevice("MapioGPIO", "mapio-gpio-769251")

        # instantiate an MQTTSwitch object for each GPIO
        self.relay1 = MqttSwitch(MqttDeviceSettings("RELAY1", "RELAY1", self.client, dev))

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
            MqttDeviceSettings("UPS Voltage", "ups", self.client, dev),
            "%",
            HaDeviceClass.BATTERY,
            True,
        )

        if self.linky_enable:
            self.linky: dict[str, Any] = {}
            for measure in HA_LINKY_MEASURES:
                self.linky[measure["exposed_variable"]] = MqttTicSensor(
                    MqttDeviceSettings(
                        f"Teleinfo {measure['exposed_variable']}",
                        measure["exposed_variable"],
                        self.client,
                        dev,
                    ),
                    measure["unit"],
                    measure["device_class"],
                    measure["state_class"],
                    True,
                )
                self.linky[measure["exposed_variable"]].pre_discovery()

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

        output = output.replace("volt=", "")
        output = output.replace("V", "")

        self.ups.publish_state(percent)

    def read_teleinfo(self, port: str = "/dev/ttyAMA3", baudrate: int = 1200) -> None:
        """Task that read teleinfo from Linky."""
        serial_port = serial.Serial(
            port,
            baudrate,
            bytesize=serial.SEVENBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
        )
        try:
            while True:
                try:
                    line = serial_port.readline().decode("utf-8").strip()
                    parsed_data = {}
                    for register in LINKY_REGISTERS:
                        if line.startswith(register["name"]):
                            parsed_data[register["name"]] = line.split(" ")[1]
                            self.logger.info(f"parsed_data {parsed_data}")
                            self.linky[register["exposed_variable"]].publish_state(
                                parsed_data[register["name"]]
                            )
                except UnicodeDecodeError:
                    self.logger.warn("Wrong formatted line received")

        except KeyboardInterrupt:
            serial_port.close()

    def close_mapio_gpio_to_ha(self) -> None:
        """Free the allocated resources."""
        # close the device for cleanup. Gets marked as offline/unavailable in homeassistant
        self.relay1_ctrl.set_value(0)
        self.relay1_ctrl.release()

        self.relay1.close()  # type: ignore
        self.ups.close()  # type: ignore
        if self.linky_enable:
            for measure in HA_LINKY_MEASURES:
                self.linky[measure["exposed_variable"]].close()

        self.led_r.close()  # type: ignore
        self.led_g.close()  # type: ignore
        self.led_b.close()  # type: ignore
        self.client.loop_stop()
        self.client.disconnect()
