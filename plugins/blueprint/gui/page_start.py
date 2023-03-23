import logging
import tkinter as tk

from ..saves import SaveComponents

logger = logging.getLogger(__name__)


class PageStart(tk.Frame):

    def __init__(self, parent, parent_app, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        # parent is the frame "container" in App. controller is the App class
        self.parent = parent
        self.parent_app = parent_app

        from .. import events
        self._saves = SaveComponents('blueprint')

        self._add_events()

    @property
    def user(self):
        return self.parent_app.user

    def startup(self):
        """
        :return:
        """
        self._build()
        self.update_page()
        self._add_to_save()

    def close(self):
        pass

    def update_page(self):
        pass

    def _add_to_save(self):
        """Added components should have a set and get method"""
        # self._saves.add_components()
        self._saves.load()

    def _add_events(self):
        pass

    def _build(self):
        pass