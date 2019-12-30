"""
__main__.py - Entry point for the application.

December 2018, Lewis Gaul
"""

import logging
import sys

from . import core, frontend, utils
from ._version import __version__


logger = logging.getLogger(__name__)

logging.basicConfig(
    filename="runtime.log",
    level=logging.DEBUG,
    format="%(asctime)s[%(levelname)s](%(name)s) %(message)s",
)


read_settings = utils.read_settings_from_file()

if read_settings:
    game_opts = utils.GameOptsStruct.from_structs(read_settings)
    gui_opts = utils.GuiOptsStruct.from_structs(read_settings)
    logger.info("Settings read from file")
else:
    logger.info("Using default settings")
    game_opts = utils.GameOptsStruct()
    gui_opts = utils.GuiOptsStruct()
logger.debug("Game options: %s", game_opts)
logger.debug("GUI options: %s", gui_opts)


logger.info("Starting up")

ctrlr = core.BaseController(game_opts)

gui = frontend.create_gui(ctrlr, gui_opts, game_opts)

ctrlr.register_listener(frontend.FrontendController(gui))

rc = frontend.run()


persist_settings = utils.AllOptsStruct.from_structs(
    ctrlr.get_game_options(), gui.get_gui_opts()
)
utils.write_settings_to_file(persist_settings)


logger.info("Exiting with exit code %d", rc)

sys.exit(rc)
