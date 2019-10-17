#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import tkinter as tk


"""
================================================================================
================================================================================
================================================================================
"""
class PageStart(tk.Frame):

    def __init__(self, parent, parent_app, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        # parent is the frame "container" in App. contoller is the App class
        self.parent = parent
        self.parent_app = parent_app

    def startup(self):
        """

        :return:
        """
        tk.Label(self, text='Startup page').grid()
        self.update_page()


    #===========================================================================
    def update_page(self):
        pass