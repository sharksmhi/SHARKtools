# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

# To use basemap you might need to install Microsoft Visual C++: https://visualstudio.microsoft.com/visual-cpp-build-tools/


import tkinter as tk
import os
import sys

import core
from sharkpylib.gismo.exceptions import *
from sharkpylib import loglib


ALL_PAGES = dict()


APP_TO_PAGE = dict()


class PluginApp(tk.Frame):
    """
    Base class for plugins to gismo_gui_tkinter
    """
    
    #===========================================================================
    def __init__(self, parent, main_app, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        # parent is the frame "container" in App. contoller is the App class
        self.parent = parent
        self.main_app = main_app
        self.version = ''

        self.info_popup = self.main_app.info_popup

        self.plugin_directory = os.path.dirname(sys.modules[self.__module__].__file__)
        self.root_directory = self.main_app.root_directory
        self.users_directory = self.main_app.users_directory
        self.log_directory = self.main_app.log_directory
        # self.mapping_files_directory = self.main_app.mapping_files_directory

    # def get_user_settings(self):
    #     """
    #     Fill to add settings objects
    #     :return: list with tuples as (settings_type, name)
    #     """
    #     raise GISMOExceptionMethodNotImplemented

    def startup(self):
        """
        Used to startup pages.
        """
        # Initiate here
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)

        self.logger = loglib.get_logger(name='default',
                                        logfiles=[dict(level='DEBUG',
                                                       file_path=os.path.join(self.log_directory, 'default_debug.log')),
                                                  dict(level='WARNING',
                                                       file_path=os.path.join(self.log_directory, 'default_warning.log')),
                                                  dict(level='ERROR',
                                                       file_path=os.path.join(self.log_directory,
                                                                               'default_error.log'))
                                                  ])

        self.paths = core.Paths(self.plugin_directory)

        # Load settings files object
        self.settings_files = core.SamplingTypeSettingsFiles(self.paths.directory_settings_files)

        # Load settings
        self.settings = self.main_app.settings

        self.user_manager = self.main_app.user_manager
        self.user = self.main_app.user

        self.all_ok = True
        
        self.active_page = None
        self.previous_page = None
        self.admin_mode = False
        self.progress_running = False
        self.progress_running_toplevel = False
        self.latest_loaded_sampling_type = ''


        # Show start page given in settings.ini
        self.page_history = ['PageUser']
        # self.show_frame('PageStart')

        self.update_page()


    def update_page(self):
        """

        :return:
        """
        raise GISMOExceptionMethodNotImplemented





