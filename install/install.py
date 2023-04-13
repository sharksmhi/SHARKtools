from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import requests
import yaml

if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).parent
elif __file__:
    ROOT_DIR = Path(__file__).parent


logger = logging.getLogger(__name__)

ORG_TAG = '<org>'
REPO_TAG = '<repo>'
TAG_TAG = '<tag>'
TAG_URL_TEMPLATE = f'https://api.github.com/repos/{ORG_TAG}/{REPO_TAG}/tags'
INSTALL_TEMPLATE = f'git+https://github.com/{ORG_TAG}/{REPO_TAG}.git@{TAG_TAG}'

VALID_PYTHON_VERSIONS = ['38']


class InvalidOption(Exception):
    pass


class Config:
    def __init__(self, config=None):
        self._config = config or dict()

    @property
    def install_directory(self) -> Path:
        return Path(self._config['install_in_directory'])

    @property
    def sharktools_directory(self) -> Path:
        return Path(self.install_directory, 'SHARKtools')

    @property
    def plugins_directory(self) -> Path:
        return Path(self.sharktools_directory, 'plugins')

    @property
    def venv_directory(self) -> Path:
        return Path(self.install_directory, 'venv')

    @property
    def temp_directory(self) -> Path:
        path = Path(self.install_directory, 'temp')
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def wheels_directory(self) -> Path:
        path = self._config['wheels_directory']
        if path:
            return Path(path)
        return Path(ROOT_DIR, 'wheels')

    @property
    def wheels_zip_path(self) -> Path:
        path = self._config['wheels_zip']
        if path:
            return Path(path)
        return Path(ROOT_DIR, 'wheels.zip')

    @property
    def use_wheels(self):
        return bool(self._config['use_wheels'] or False)

    @property
    def install_venv_bat_path(self) -> Path:
        return Path(self.install_directory, 'install_venv.bat')

    @property
    def run_bat_path(self) -> Path:
        return Path(self.install_directory, 'run.bat')

    @property
    def requirements_file_path(self) -> Path:
        return Path(self.install_directory, 'install_requirements.txt')

    @property
    def python_version(self):
        version = str(self._config['python_version']).replace('.', '')
        if version not in VALID_PYTHON_VERSIONS:
            raise Exception(f'Invalid python version {version}')
        return version

    @property
    def python_path(self) -> Path:
        path = Path(self._config['path_to_python'])
        if path.is_dir():
            path = Path(path, 'python.exe')
        if not path.exists():
            raise FileNotFoundError(path)
        return path

    @property
    def repos(self) -> dict:
        return self._config['repos']

    @property
    def wheels(self) -> list:
        return self._config['wheels']

    def get(self, repo) -> str:
        """Returns the config setting for the given repo"""
        return self._config['repos'][repo]

    def unpack_wheels(self):
        if self.wheels_directory.exists():
            logger.info(f'Wheels directory does already exist. Delete this directory if you want to update: '
                        f'{self.wheels_directory}')
            return
        with zipfile.ZipFile(self.wheels_zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.wheels_directory.parent)

    @classmethod
    def from_config_file(cls, path):
        with open(path) as fid:
            config = yaml.safe_load(fid)
        return Config(config)


class Tag:
    org_name = None
    repo_name = None
    name = None
    zipball_url = None
    tarball_url = None
    commit = None
    node_id = None

    def __init__(self, org_name, repo_name, info):
        self.org_name = org_name
        self.repo_name = repo_name
        for key, value in info.items():
            setattr(self, key, value)

    def __str__(self):
        return f'{__class__.__name__}: {self.repo_name}-{self.name}'

    @property
    def install_line(self):
        return INSTALL_TEMPLATE.replace(ORG_TAG,
                                        self.org_name).replace(REPO_TAG,
                                                               self.repo_name).replace(TAG_TAG, self.name)

    def download_to_directory(self, directory):
        target_dir = Path(directory, self.repo_name)
        if target_dir.exists():
            shutil.rmtree(target_dir)
        with tempfile.TemporaryDirectory() as tempdir:
            r = requests.get(self.zipball_url, allow_redirects=True)
            temp_zip_path = Path(tempdir, f'{self.name}.zip')
            with open(temp_zip_path, 'wb') as fid:
                fid.write(r.content)
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(tempdir)
            for source_path in Path(tempdir).iterdir():
                if self.repo_name in source_path.name:
                    shutil.copytree(str(source_path), str(target_dir))
                    return target_dir


class Repo:
    def __init__(self, org_name, repo_name):
        self._org = org_name
        self._repo = repo_name
        self._tags = {}

        self._load_tags()

    def __str__(self):
        return f'{__class__.__name__}: {self._repo}'

    @property
    def local_tags_file(self):
        return Path(ROOT_DIR, 'tags.yaml')

    @property
    def _load_tag_info(self):
        with open(self.local_tags_file) as fid:
            data = yaml.safe_load(fid)
        return data.get(self._repo)

    def _save_tag_info(self, tag_list):
        with open(self.local_tags_file) as fid:
            data = yaml.safe_load(fid)
        data[self._repo] = tag_list
        with open(self.local_tags_file, 'w') as fid:
            yaml.dump(data, fid)

    @property
    def tags(self):
        return sorted(self._tags)

    @property
    def tag_url(self):
        return TAG_URL_TEMPLATE.replace(ORG_TAG, self._org).replace(REPO_TAG, self._repo)

    @property
    def options(self):
        return self.tags

    def _get_tags_info_list(self):
        response = requests.get(self.tag_url).json()
        if type(response) != list:
            return self._get_tags_info_list()
        self._save_tag_info(response)
        return response

    def _load_tags(self):
        for tag_info in self._get_tags_info_list():
            tag = Tag(self._org, self._repo, tag_info)
            self._tags[tag.name] = tag

    def download_tag(self, tag, directory):
        return self._tags[tag].download_to_directory(directory)

    def get_tag_install_line(self, tag):
        if not tag:
            return INSTALL_TEMPLATE.replace(ORG_TAG, self._org).replace(REPO_TAG, self._repo).split('@')[0]
        return self._tags[tag].install_line


class InstallSHARKtools:

    def __init__(self):
        self._install_directory = None
        self._wheels_directory = None
        self._repos = {}
        self._settings = {}
        self._config = None
        self._req = None
        self._install_venv_bat = None
        self._run_bat = None

        self._load_settings()
        self._load_repos()

    @property
    def settings_file(self):
        return Path(ROOT_DIR, 'install_settings.yaml')

    @property
    def settings(self):
        return self._settings

    @property
    def config(self):
        return self._config

    @property
    def organisation(self):
        return self.settings['organisation']

    @property
    def main(self):
        return self.settings['repos']['main']

    @property
    def plugins(self):
        return self.settings['repos']['plugins']

    @property
    def help_repos(self):
        return self.settings['repos']['help_repos']

    def _load_settings(self):
        with open(self.settings_file) as fid:
            self._settings = yaml.safe_load(fid)

    def _load_repos(self):
        for key, value in self.settings['repos'].items():
            if isinstance(value, list):
                for repo in value:
                    self._repos[repo] = Repo(self.organisation, repo)
            else:
                self._repos[key] = Repo(self.organisation, value)

    def get_options(self):
        options = {}
        options['main'] = {}
        options['main'][self.main] = self._repos['main'].options

        options['plugins'] = {}
        for plug in self.plugins:
            options['plugins'][plug] = self._repos[plug].options

        options['help_repos'] = {}
        for hrepo in self.help_repos:
            options['help_repos'][hrepo] = self._repos[hrepo].options

        return options

    @property
    def repos(self):
        return self._repos

    def _is_valid_option(self, repo, option):
        if option in self.repos[repo].options:
            return True
        return False

    # def _download_tag_for_repo(self, tag, repo, directory):
    #     return self.repos[repo].download_tag(tag, directory)

    def load_config(self, path):
        self._config = Config.from_config_file(path)

    def install(self):
        self._download_main()
        self._download_plugins()
        self._create_install_venv_bat_file()
        self._create_requirements_file()
        self._run_install_venv_bat()
        self._create_run_bat_file()

    def _download_main(self):
        self.config.install_directory.mkdir(parents=True, exist_ok=True)
        repo = 'SHARKtools'
        if repo not in self.config.repos:
            return
        if self.config.sharktools_directory.exists():
            logger.warning('Main program folder exists')
            return
        tag = self.config.get(repo)
        self._repos['main'].download_tag(tag, self.config.install_directory)
        self._add_version_file(tag, self.config.sharktools_directory)

    def _download_plugins(self):
        for plugin in self.plugins:
            tag = self.config.repos.get(plugin)
            if not tag:
                print(f'No tags found for plugin {plugin}. Plugin not installed!')
                continue
            print(f'Installing plugin {plugin}')
            saves_path = self._create_saves_backup(plugin)
            path = self._repos[plugin].download_tag(tag, self.config.plugins_directory)
            self._add_version_file(tag, path)
            if saves_path:
                target_path = Path(path, 'saves.json')
                shutil.copy2(saves_path, target_path)

    def _create_saves_backup(self, plugin):
        source_path = Path(self.config.plugins_dlirectory, plugin, 'saves.json')
        if not source_path.exists():
            return
        target_path = Path(self.config.temp_directory, f'{plugin}_{source_path.name}')
        shutil.copy2(source_path, target_path)
        return target_path

    def _create_requirements_file(self):
        self._req = RequirementsFile(self, self.config)
        self._req.create_file()

    def _create_install_venv_bat_file(self):
        self._install_venv_bat = InstallVenvBat(self.config)
        self._install_venv_bat.create_file()

    def _create_run_bat_file(self):
        self._run_bat = RunBat(self.config)
        self._run_bat.create_file()

    def _run_install_venv_bat(self):
        subprocess.run([self.config.install_venv_bat_path])

    def _add_version_file(self, tag, directory):
        root = Path(directory)
        version_path = Path(directory, f'__version__{tag}')
        for path in root.iterdir():
            if path.name.startswith('__version__'):
                if path.name == version_path.name:
                    logger.info(f'Same version file exists: {path}')
                    return
                else:
                    logger.error(f'Old version file found: {path} should be {version_path}')
                    raise
        with open(version_path, 'w') as fid:
            pass
        

class RequirementsFile:
    def __init__(self, install: InstallSHARKtools, config: Config):
        self.install = install
        self.config = config

    def create_file(self):
        lines = []
        lines.extend(self._get_main_program_requirement_lines())
        lines.extend(self._get_plugins_requirement_lines())
        lines.extend(self._get_wheel_lines())
        lines.extend(self._get_help_repo_lines())
        # for line in lines:
        #     self._create_and_run_pip_install_venv_bat(line)

        with open(self.config.requirements_file_path, 'w') as fid:
            fid.write('\n'.join(lines))

    def _get_wheel_lines(self):
        lines = []
        if not self.config.use_wheels:
            return lines
        self.config.unpack_wheels()
        lower_wheels_list = [item.lower() for item in self.config.wheels]
        wheels_mapping = {}
        for path in self.config.wheels_directory.iterdir():
            wheel = path.name.split('-')[0].lower()
            wheels_mapping.setdefault(wheel, [])
            wheels_mapping[wheel].append(path)
        for wheel in lower_wheels_list:
            for path in wheels_mapping[wheel]:
                if f'cp{self.config.python_version}' in path.name or 'none-any' in path.name:
                    lines.append(str(path))
        return lines

    def _get_help_repo_lines(self):
        lines = []
        for hrepo, tag in self.config.repos.items():
            if not self.install.repos.get(hrepo):
                logger.warning(f'No help_repo named {hrepo}. Will not install!')
                continue
            lines.append(self.install.repos[hrepo].get_tag_install_line(tag))
        return lines

    # def _get_help_repo_lines(self):
    #     lines = []
    #     for hrepo in self.install.help_repos:
    #         tag = self.config.repos.get(hrepo)
    #         if not tag:
    #             continue
    #         lines.append(self.install.repos[hrepo].get_tag_install_line(tag))
    #     return lines

    def _get_main_program_requirement_lines(self):
        path = Path(self.config.sharktools_directory, 'requirements.txt')
        return self._get_lines_from_file(path)

    def _get_plugins_requirement_lines(self):
        lines = []
        for dirpath in self.config.plugins_directory.iterdir():
            if not dirpath.is_dir():
                continue
            path = Path(dirpath, 'requirements.txt')
            lines.extend(self._get_lines_from_file(path))
        return lines

    def _get_lines_from_file(self, path):
        if not path.exists():
            return []
        lines = []
        with open(path) as fid:
            for line in fid:
                line = line.strip()
                if not line:
                    continue
                lines.append(line)
        return lines


class RunBat:
    def __init__(self, config: Config):
        self.config = config

    def create_file(self):
        lines = [
            f'ECHO -- Activating {self.config.venv_directory} --',
            rf'call {self.config.venv_directory}\Scripts\activate',
            f'python {self.config.sharktools_directory}/main.py',
            'ECHO.',
            ''
        ]
        with open(self.config.run_bat_path, 'w') as fid:
            fid.write('\n'.join(lines))


class InstallVenvBat:
    def __init__(self, config: Config):
        self.config = config
    
    def create_file(self):
        lines = []
        lines.extend(self._get_bat_lines_create_venv())
        lines.extend(self._get_bat_lines_activate_venv())
        lines.extend(self._get_bat_lines_install_requirements())
        with open(self.config.install_venv_bat_path, 'w') as fid:
            fid.write('\n'.join(lines))
            
    def _get_bat_lines_create_venv(self):
        lines = [
            'ECHO ON',
            'cls',
            f'cd {self.config.sharktools_directory}',
            'ECHO.',
            '',
            'ECHO -- Creating virtual environment --',
            rf'if exist {self.config.venv_directory}/ (',
            'ECHO Virtual environment already exists',
            ') else (',
            f'ECHO Creating virtual environment at {self.config.venv_directory} using {self.config.python_path}',
            f'{self.config.python_path} -m venv {self.config.venv_directory}',
            ')',
            'ECHO.',
            ''
        ]
        return lines

    def _get_bat_lines_activate_venv(self):
        lines = [
            f'ECHO -- Activating {self.config.venv_directory} --',
            rf'call {self.config.venv_directory}\Scripts\activate',
            'python -m pip install --upgrade pip',
            'ECHO.',
            ''
        ]
        return lines

    def _get_bat_lines_install_requirements(self):
        lines = [
            f'ECHO -- Installing requirements --',
            # f'cd {self.config.sharktools_directory}',
            # 'pip install -r requirements.txt',
            'ECHO.',
            f'cd {self.config.install_directory}',
            f'pip install --no-cache-dir -r {self.config.requirements_file_path}',
            ''
        ]
        return lines


def main():
    inst = InstallSHARKtools()
    for path in Path(ROOT_DIR).iterdir():
        if path.suffix == '.yaml' and path.name.startswith('config'):
            print(f'Loading config file: {path}')
            inst.load_config(path)
            inst.install()
            return


if __name__ == '__main__':
    if 0:
        main()
    else:
        inst = InstallSHARKtools()
        inst.load_config(r'./test_config.yaml')
        #inst.install()



