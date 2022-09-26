# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
import datetime
import json
import logging
import os
import shutil
import socket
from pathlib import Path

import pandas as pd

from core.exceptions import *

gui_logger = logging.getLogger('gui_logger')


class UserManager(object):
    def __init__(self, users_root_directory=None, app_root_directory=None):
        self.users_root_directory = users_root_directory
        self.app_root_directory = app_root_directory
        self.current_user_directory = None
        self.directory_user_settings = {}
        self.users = {}
        self.user = None
        self.app_settings = None

        self._load_app_settings()

    def _load_app_settings(self):
        self.app_settings = AppSettings(directory=self.users_root_directory,
                                        name='app_settings',
                                        app_root_directory=self.app_root_directory)

    def set_users_directory(self, users_directory):
        self.current_user_directory = users_directory
        if not self.current_user_directory.exists():
            os.mkdir(self.current_user_directory)
        self.users = {}
        users_directory = Path(users_directory).absolute()
        # for user in os.listdir(users_directory):
        for user in users_directory.iterdir():
            if not user.is_dir():
                continue
            # if user == '.active':
            #     continue
            # print('user', user, users_directory)
            # if not Path(user).is_dir():
            #     print('NOT', Path(user))
            #     continue
            # print('YES')
            self.users[user.name] = User(user.name, self.current_user_directory)
            directory_dict = self.directory_user_settings.get(self.current_user_directory, {})
            for settings_type in directory_dict:
                # print('--', settings_type)
                for item in directory_dict[settings_type]:
                    # print('---', item)
                    self.users[user.name].add_user_settings(settings_type, **item)
        try:
            self.set_active_user()
        except GUIExceptionUserError:
            pass

    def set_user(self, user_name, create_if_missing=False):
        if user_name not in self.users:
            if create_if_missing:
                self.add_user(user_name)
            else:
                raise GUIExceptionUserError('Invalid user name: {}'.format(user_name))
        self.user = self.users.get(user_name)
        self._save_active_user(user_name)

    def get_user_list(self):
        return sorted(self.users)

    def add_user(self, user_name, from_user=None):
        if user_name in self.users:
            raise GUIExceptionUserError('User already exists')
        if from_user:
            if from_user not in self.users:
                raise GUIExceptionUserError('Could not find source user')
            from_dir = Path(self.current_user_directory, from_user)
            to_dir = Path(self.current_user_directory, user_name)
            shutil.copytree(str(from_dir), str(to_dir))
        else:
            # New user
            pass
        self.users[user_name] = User(user_name, self.current_user_directory)

    def add_user_settings(self, users_directory=None, settings_type=None, settings_name=None, **kwargs):
        self.directory_user_settings.setdefault(users_directory, {})
        kw = dict(name=settings_name)
        kw.update(kwargs)
        if settings_type == 'basic':
            self.directory_user_settings[users_directory].setdefault('basic', [])
            self.directory_user_settings[users_directory]['basic'].append(kw)
        elif settings_type == 'parameter':
            self.directory_user_settings[users_directory].setdefault('parameter', [])
            self.directory_user_settings[users_directory]['parameter'].append(kw)
        elif settings_type == 'prioritylist':
            self.directory_user_settings[users_directory].setdefault('prioritylist', [])
            self.directory_user_settings[users_directory]['prioritylist'].append(kw)

    def get_default_user_settings(self, settings, key):
        try:
            user = self.users['default']
            settings = getattr(user, settings)
            value = settings.get(key)
            return value
        except:
            return None

    def get_app_settings(self, par, key, default_value=None):
        return self.app_settings.setdefault(par, key, default_value)

    def set_app_settings(self, par, key, value):
        self.app_settings.set(par, key, value)

    def set_default_user(self):
        self.set_user('default')

    def set_active_user(self):
        active_user = self._get_active_user()
        self.set_user(active_user)

    def _get_active_user_file_path(self):
        return Path(self.current_user_directory, '.active')

    def _get_active_user(self, user_directory=None):
        if user_directory:
            file_path = Path(user_directory, '.active')
        else:
            file_path = self._get_active_user_file_path()
        if not file_path.exists():
            active_user = socket.gethostname()
        else:
            with open(file_path) as fid:
                active_user = fid.readline().strip()
        return active_user

    def _save_active_user(self, user):
        file_path = self._get_active_user_file_path()
        with open(file_path, 'w') as fid:
            fid.write(user)


class User(object):
    def __init__(self, name, users_root_directory, **kwargs):
        self._name = name
        # print(self.name)
        self.user_directory = os.path.join(users_root_directory, self.name)
        if not os.path.exists(self.user_directory):
            os.mkdir(self.user_directory)

    @property
    def name(self):
        return self._name

    def add_user_settings(self, settings_type, **kwargs):
        if settings_type == 'basic':
            obj = UserSettings(directory=self.user_directory, user=self.name, **kwargs)
        elif settings_type == 'parameter':
            obj = UserSettingsParameter(directory=self.user_directory, user=self.name, **kwargs)
        elif settings_type == 'prioritylist':
            obj = UserSettingsPriorityList(directory=self.user_directory, user=self.name, **kwargs)
        setattr(self, obj.name, obj)


class UserSettings(object):
    """
    Baseclass for user settings.
    """
    def __init__(self, directory=None, name=None, user=None, time_string_format='%Y-%m-%d %H:%M:%S'):
        self.directory = directory
        self.name = name
        self.user = user
        self.file_path = os.path.join(self.directory, '{}.json'.format(self.name))
        self.time_string_format = time_string_format
        self.data = {}

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        if not os.path.exists(self.file_path):
            self.save()

        self._load()

    def _load(self):
        """
        Loads dict from json
        :return:
        """
        if os.path.exists(self.file_path):
            with open(self.file_path) as fid:
                self.data = json.load(fid)
        self.datestring_to_datetime()

    def datestring_to_datetime(self):
        for key, value in self.data.items():
            if 'time' in key:
                if value:
                    self.data[key] = datetime.datetime.strptime(value, self.time_string_format)

    def datetime_to_datestring(self):
        for key, value in self.data.items():
            if 'time' in key:
                if value:
                    self.data[key] = pd.to_datetime(value).strftime(self.time_string_format)

    def path_to_string(self):
        for key, value in self.data.items():
            if isinstance(value, Path):
                self.data[key] = str(value)

    def save(self):
        """
        Writes information to json file.
        :return:
        """
        # if self.user == 'default':
        #     return
        # Convert datetime object to str
        self.datetime_to_datestring()

        # Convert Paths
        self.path_to_string()
        # print('=' * 20)
        # print('SAVE')
        # for key in sorted(self.data):
        #     print(key, type(self.data[key]), self.data[key])
        #     import datetime
        #
        # print('=' * 20)
        with open(self.file_path, 'w') as fid:
            json.dump(self.data, fid)
        self.datestring_to_datetime()

    def get(self, key, if_missing=None):
        """

        :param key:
        :return:
        """
        gui_logger.debug('USER-get: {}; {}, {}, {}'.format(self.name, key, type(self.data.get(key, if_missing)), self.data.get(key, if_missing)))
        return self.data.get(key, if_missing)

    def get_keys(self):
        return self.data.keys()

    def setdefault(self, key, value, save=True):
        """
        Works as setdefault for a dictionary. Should always be called with key and value.
        If data is set (key not in self.data) the dictionary is saved to json file.
        :param key:
        :param value:
        :return:
        """
        if self.user == 'default':
            raise GUIExceptionUserError('Cannot change default user')
        gui_logger.debug('USER-setdefault: {}; {}, {}, {}'.format(self.name, key, type(value), value))
        if self.data.get(key):
            return self.data.get(key)
        else:
            value = self.data.setdefault(key, value)
            if save:
                self.save()
            return value

    def set(self, key, value, save=True):
        """
        Sets key to value
        :param key:
        :param value:
        :return:
        """
        if self.user == 'default':
            return
        if key not in self.data:
            self.data.setdefault(key, value)
        else:
            self.data[key] = value
        if save:
            self.save()

    def get_settings(self):
        """
        Returns the whole dictionary self.data
        :return:
        """
        return self.data

    def remove(self, key):
        if self.user == 'default':
            return
        if key in self.data:
            self.data.pop(key)
            self.save()

    def reset(self):
        if self.user == 'default':
            return
        self.data = {}
        self.save()


class UserSettingsParameter(UserSettings):
    def __init__(self, directory=None, name=None, user=None, **kwargs):
        UserSettings.__init__(self, directory=directory, name=name, user=user, **kwargs)

    def setdefault(self, par, key, value, save=True):
        """
        Works as setdefault for a dictionary. Should always be called with key and value.
        If data is set (key not in self.data) the dictionary is saved to json file.
        :param key:
        :param value:
        :return:
        """
        if self.user == 'default':
            return
        self.data.setdefault(par, {})
        value = self.data[par].setdefault(key, value)
        if save:
            self.save()
        return value

    def set(self, par, key, value, save=True):
        """
        Sets key to value for parameter par
        :param par:
        :param key:
        :param value:
        :return:
        """
        if self.user == 'default':
            return
        self.data.setdefault(par, {})
        self.data[par].setdefault(key, value)
        self.data[par][key] = value
        if save:
            self.save()

    def get(self, par, key):
        """

        :param par:
        :param key:
        :return:
        """
        return self.data.get(par, {}).get(key, None)

    def get_settings(self, par=None):
        """
        Returns the whole dictionary self.data. If par is given self.data[par] is returned
        :param par:
        :return:
        """
        if par:
            return self.data.get(par, {})
        else:
            return self.data

    def datestring_to_datetime(self):
        for par in self.data:
            for key, value in self.data[par].items():
                if 'time' in key:
                    if value:
                        self.data[par][key] = datetime.datetime.strptime(value, self.time_string_format)

    def datetime_to_datestring(self):
        for par in self.data:
            for key, value in self.data[par].items():
                if 'time' in key:
                    if value:
                        self.data[par][key] = pd.to_datetime(value).strftime(self.time_string_format)


class AppSettings(UserSettingsParameter):
    def __init__(self, directory=None, app_root_directory=None, name=None, user=None, **kwargs):
        self.app_root_directory = app_root_directory
        UserSettingsParameter.__init__(self, directory=directory, name=name, user=user, **kwargs)

    def _convert_root_to_path(self, path):
        new_path = Path(str(path).replace('root', str(self.app_root_directory)))
        return new_path

    def _convert_path_to_root(self, path):
        new_path = str(path).replace(str(self.app_root_directory), 'root')
        return new_path

    def setdefault(self, par, key, value, save=True):
        """
        Works as setdefault for a dictionary. Should always be called with key and value.
        If data is set (key not in self.data) the dictionary is saved to json file.
        :param key:
        :param value:
        :return:
        """
        if self.user == 'default':
            return

        if par == 'directory':
            value = self._convert_path_to_root(value)

        self.data.setdefault(par, {})
        value = self.data[par].setdefault(key, value)
        if save:
            self.save()

        if par == 'directory':
            value = self._convert_root_to_path(value)
        return value

    def set(self, par, key, value, save=True):
        """
        Sets key to value for parameter par
        :param par:
        :param key:
        :param value:
        :return:
        """
        if self.user == 'default':
            return

        if par == 'directory':
            value = self._convert_path_to_root(value)

        self.data.setdefault(par, {})
        self.data[par].setdefault(key, value)
        self.data[par][key] = value
        if save:
            self.save()

    def get(self, par, key):
        """

        :param par:
        :param key:
        :return:
        """
        value = self.data.get(par, {}).get(key, None)
        if par == 'directory':
            value = self._convert_root_to_path(value)
        return value

    def get_settings(self, par=None):
        """
        Returns the whole dictionary self.data. If par is given self.data[par] is returned
        :param par:
        :return:
        """
        if par:
            return self.data.get(par, {})
        else:
            return self.data

    def datestring_to_datetime(self):
        for par in self.data:
            for key, value in self.data[par].items():
                if 'time' in key:
                    if value:
                        self.data[par][key] = datetime.datetime.strptime(value, self.time_string_format)

    def datetime_to_datestring(self):
        for par in self.data:
            for key, value in self.data[par].items():
                if 'time' in key:
                    if value:
                        self.data[par][key] = pd.to_datetime(value).strftime(self.time_string_format)


class UserSettingsPriorityList(UserSettings):
    def __init__(self, directory=None, name=None, user=None, **kwargs):
        UserSettings.__init__(self, directory=directory, name=name, user=user, **kwargs)

        self.data.setdefault('priority_list', [])
        self.save()

    def set_priority(self, item):
        if self.user == 'default':
            return
        if item in self.data['priority_list']:
            self.data['priority_list'].pop(self.data['priority_list'].index(item))
        self.data['priority_list'].insert(0, item)
        self.save()

    def get_priority(self, check_in_list):
        for item in self.data['priority_list']:
            if item in check_in_list:
                return item
        # Return parameter starting with Chlo
        for item in check_in_list:
            if item.lower().startswith('chl'):
                self.set_priority(item)
                return item
        return check_in_list[0]