"""Console script for mapio_gpio_ha."""

# Standard lib imports
import logging
import logging.config
import sys
import threading
import time
from pathlib import Path
from typing import Optional

# Third-party lib imports
import click  # type: ignore

from mapio_gpio_ha.app.app import MAPIO_GPIO

# Local package imports


# Define this function as a the main command entrypoint
@click.group()
# Create an argument that expects a path to a valid file
@click.option(
    "--log-config",
    help="Path to the log config file",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
)
# Display the help if no option is provided
@click.help_option()
def main(
    log_config: Optional[str],
) -> None:
    """Console script for mapio_gpio_ha."""
    if log_config is not None:
        logging.config.fileConfig(log_config)
    else:
        # Default to some basic config
        log_config = f"{Path(__file__).parent}/log.cfg"
        logging.config.fileConfig(log_config)
        tmp_logger = logging.getLogger(__name__)
        tmp_logger.warning("No log config provided, using default configuration")
    logger = logging.getLogger(__name__)
    logger.info("Logger initialized")


@main.command()
def app() -> None:
    """App entrypoint."""
    logger = logging.getLogger(__name__)
    logger.info("Start mapio gpio to HA")
    enable_linky = False
    if Path("/usr/local/homeassistant/enable_linky").exists():
        logger.info("Enable linky teleinfo module")
        enable_linky = True
    mapio_gpio = MAPIO_GPIO()
    mapio_gpio.expose_mapio_gpio_to_ha(enable_linky)

    if enable_linky:
        thread = threading.Thread(target=mapio_gpio.read_teleinfo)
        thread.start()
    try:
        while True:
            mapio_gpio.refresh_mapio_gpio_to_ha()
            time.sleep(30)
    except KeyboardInterrupt:
        pass
    finally:
        mapio_gpio.close_mapio_gpio_to_ha()


if __name__ == "__main__":
    sys.exit(main())
