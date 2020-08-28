# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

# To use basemap you might need to install Microsoft Visual C++: https://visualstudio.microsoft.com/visual-cpp-build-tools/


import os
import tkinter as tk

import sharkpylib.tklib.tkinter_widgets as tkw

import core
from plugins.blueprint import gui
from plugins.plugin_app import PluginApp

ALL_PAGES = dict()
ALL_PAGES['PageStart'] = gui.PageStart
ALL_PAGES['PageUser'] = gui.PageUser

APP_TO_PAGE = dict()
for page_name, page in ALL_PAGES.items():
    APP_TO_PAGE[page] = page_name


class App(PluginApp):
    """
    """
    
    #===========================================================================
    def __init__(self, parent, main_app, **kwargs):
        PluginApp.__init__(self, parent, main_app, **kwargs)
        # parent is the frame "container" in App. contoller is the App class
        self.parent = parent
        self.main_app = main_app
        self.version = ''

        self.info_popup = self.main_app.info_popup
        self.plugin_directory = os.path.dirname(os.path.abspath(__file__))
        self.root_directory = self.main_app.root_directory
        self.log_directory = self.main_app.log_directory
        # self.mapping_files_directory = self.main_app.mapping_files_directory

    # def get_user_settings(self):
    #     return [('basic', 'test')]

    def startup(self):
        """
        """
        # Setting upp GUI logger
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)

        self.logger = self.main_app.logger

        self.paths = core.Paths(self.plugin_directory)

        # Load settings files object
        self.settings_files = core.SamplingTypeSettingsFiles(self.paths.directory_settings_files)

        self.settings = self.main_app.settings

        self.user_manager = self.main_app.user_manager
        self.user = self.main_app.user

        self._create_titles()

        self.all_ok = True
        
        self.active_page = None
        self.previous_page = None
        self.admin_mode = False
        self.progress_running = False
        self.progress_running_toplevel = False

        self.latest_loaded_sampling_type = ''

        self._set_frame()

        self.startup_pages()

        self.page_history = ['PageUser']
        self.show_frame('PageStart')

        self.update_all()


    def update_page(self):
        self.update_all()

    #==========================================================================
    def _set_frame(self):
        self.frame_top = tk.Frame(self, bg='red')
        self.frame_mid = tk.Frame(self, bg='green')
        self.frame_bot = tk.Frame(self, bg='blue')

        
        # Grid
        self.frame_top.grid(row=0, column=0, sticky="nsew")
        self.frame_mid.grid(row=1, column=0, sticky="nsew")
        self.frame_bot.grid(row=2, column=0, sticky="nsew")
        
        # Gridconfigure 
        tkw.grid_configure(self, nr_rows=3, r0=100, r1=5, r2=1)
        
        #----------------------------------------------------------------------
        # Frame top
        # Create container in that will hold (show) all frames
        self.container = tk.Frame(self.frame_top)
        self.container.grid(row=0, column=0, sticky="nsew") 
        tkw.grid_configure(self.frame_top)

        
        #----------------------------------------------------------------------
        # Frame mid
        self.frame_add = tk.LabelFrame(self.frame_mid)
        self.frame_loaded = tk.LabelFrame(self.frame_mid, text='Loaded files')
        
        # Grid
        self.frame_add.grid(row=0, column=0, sticky="nsew")
        self.frame_loaded.grid(row=0, column=1, sticky="nsew")
        
        # Gridconfigure 
        tkw.grid_configure(self.frame_mid, nr_columns=2)
        
        #----------------------------------------------------------------------
        # Frame bot
        self._set_frame_bot()


    def _set_frame_bot(self):
        self.frame_info = tk.Frame(self.frame_bot)
        self.frame_info.grid(row=0, column=0, sticky="nsew")

        # ttk.Separator(self.frame_bot, orient=tk.VERTICAL).grid(row=0, column=1, sticky='ns')

        self.frame_progress = tk.Frame(self.frame_bot)
        # self.frame_progress.grid(row=0, column=2, sticky="nsew")
        self.progress_widget = tkw.ProgressbarWidget(self.frame_progress, sticky='nsew')

        self.info_widget = tkw.LabelFrameLabel(self.frame_info, pack=False)

        tkw.grid_configure(self.frame_info)
        tkw.grid_configure(self.frame_bot)


    #===========================================================================
    def startup_pages(self):
        # Tuple that store all pages
        
        self.pages_started = dict()
        
        
        # Dictionary to store all frame classes
        self.frames = {}
        
        # Looping all pages to make them active. 
        for page_name, Page in ALL_PAGES.items():  # Capital P to emphasize class
            # Destroy old page if called as an update
            try:
                self.frames[page_name].destroy()
                print(Page, u'Destroyed')
            except:
                pass
            frame = Page(self.container, self)
            frame.grid(row=0, column=0, sticky="nsew")

            self.container.rowconfigure(0, weight=1)
            self.container.columnconfigure(0, weight=1) 
            
            self.frames[page_name] = frame

    def _set_load_frame(self):
        pass

    def update_all(self):
        for page_name, frame in self.frames.items():
            if self.pages_started.get(page_name):
                # print('page_name', page_name)
                frame.update_page()

    def show_frame(self, page_name):
        """
        This method brings the given Page to the top of the GUI. 
        Before "raise" call frame startup method. 
        This is so that the Page only loads ones.
        """

        load_page = True
        frame = self.frames[page_name]
        # self.withdraw()
        if not self.pages_started.get(page_name, None):
            frame.startup()
            self.pages_started[page_name] = True
        frame.update_page()

        #-----------------------------------------------------------------------
        if load_page:
            frame.tkraise()
            self.previous_page = self.active_page
            self.active_page = page
            # Check page history
            if page in self.page_history:
                self.page_history.pop()
                self.page_history.append(page)
        self.update()



    #===========================================================================
    def goto_previous_page(self, event):
        self.page_history
        if self.previous_page:
            self.show_frame(self.previous_page) 
        
    #===========================================================================
    def previous_page(self, event):
        self.page_history.index(self.active_page)
        
    
    #===========================================================================
    def update_app(self):
        """
        Updates all information about loaded series. 
        """
        self.update_all()


    #===========================================================================
    def _get_title(self, page):
        if page in self.titles:
            return self.titles[page]
        else:
            return ''
    
    #===========================================================================
    def _create_titles(self):
        self.titles = {}





