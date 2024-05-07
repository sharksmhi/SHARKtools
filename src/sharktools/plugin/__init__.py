# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
import os
import importlib

from .plugin_app import PluginApp

# PLUGIN_LIST = [p for p in os.listdir(os.path.dirname(__file__)) if not '.' in p and not p.startswith('__')]
#
# PLUGIN_LIST.pop(PLUGIN_LIST.index('blueprint'))

# for plugin in PLUGIN_LIST:
#     importlib.import_module('plugins.{}'.format(plugin))
