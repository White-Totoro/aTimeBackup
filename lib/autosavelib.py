import datetime as dt
import os
import shutil
from pathlib import Path
import platform

import nuke

__all__ = ("date", "file", "script", "local", "save", "preferences")

_NUKE_PREFERENCES = nuke.toNode("preferences")
_OS_NAME = platform.system()


class date:
    """
    Provides different time formats for creating checkpoints, folder
    names and recording the time at which an autosave file was backed up.
    """

    __slots__ = ["date"]

    def __init__(self, date: object) -> None:
        """
        Takes one argumnet in datetime object format
        @date - datetime object
        """
        self.date = date

    @property
    def today(self) -> str:
        """
        Return today's date in format: %Y%m%d
        %Y - year
        %m - month
        %d - day
        """
        return self.date.strftime("%Y%m%d")

    @classmethod
    def str2time(cls, string_time: str, date_format: str) -> object:
        """
        Convert string to time object
        @date_object - checkpoint value
        """
        return dt.datetime.strptime(string_time, date_format)

    @classmethod
    def get_time(cls) -> str:
        """
        Returns the time for the checkpoint as a string
        """
        return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _time2str(self, date_object: object, date_format: str) -> str:
        """
        Convert datetime object to string
        @date_object - datetime object
        @date_format - string pattern(%H:%M:%S)
        """
        return date_object.strftime(date_format)

    def name_time(self) -> str:
        """
        Generate the time in the format _%H-%M-%S for the backup name
        """
        return self._time2str(self.date, "_%H-%M-%S")


class file:
    """
    Gives access to autosave a file and get the directory of its parent.
    Generates a new name with the time of file saving.
    """

    __slots__ = ["as_file"]

    def __init__(self, as_file: str) -> None:
        """
        Path to the autosave file. You can use get_file() method
        to get the location of the file.
        @as_file
        """
        self.as_file = as_file

    @classmethod
    def get_file(cls):
        """
        Takes the autosave path from the nuke settings and returns it.
        """
        return _NUKE_PREFERENCES["AutoSaveName"].evaluate()

    @classmethod
    def exists_file(cls) -> bool:
        """
        Check for the presence of a file in a folder to avoid backup errors
        """
        if Path(cls.get_file()).exists():
            return True
        else:
            return False

    @property
    def parents(self) -> str:
        """
        Returns the folder of the autosave file
        """
        return self._get_parents(self.as_file)

    @property
    def name(self) -> str:
        """
        Returns name autosave file without extensions
        """
        return self._get_raw_name(self.as_file)

    def _get_parents(self, file) -> str:
        """
        Strips the file name form the path
        """
        return ("/").join(file.split("/")[:-1])

    def _get_raw_name(self, file) -> str:
        """
        Cut off the file path and extensions
        """
        return file.split("/")[-1].split(".")[0]

    def add_time_to_name(self, name, date):
        return name + date

    def merge(self, path, file) -> object:
        """
        Join the path with the file nad return the path object
        """
        return Path(path, file)

    def add_ext(self, name) -> str:
        """
        Append extensions to the name:
        .nk
        .autosave
        """
        ext_list = ["nk", "autosave"]
        ext_list.insert(0, name)
        return (".").join(ext_list)


class _folder:
    """
    The base class for the script and local subclasses.
    Check for directory, search for early files and check
    for number of copies
    """

    __slots__ = ["path", "date"]

    def __init__(self, path: str, date: str) -> None:
        """
        Takes two arguments
        @path - autosave directory path
        @date - today date(use property date(dt.datetime.now()).today)
        """
        self.path = path
        self.date = date

    @property
    def autosave_path(self) -> object:
        """
        Returns the autosave backup directory. - ".../.autosave/date(dt.datetime.now()).today"
        """
        return Path(self.path, ".autosave", self.date)

    @classmethod
    def _local_folder(cls) -> object:
        home = Path().home()
        return Path(home, ".nuke")

    def exists(self, path) -> None:
        """
        Checks to see if the folder exists. And creating it if it doesn't exist
        """

        input_path = Path(path)
        if not input_path.exists():
            input_path.mkdir(parents=True)

    def find_early_file(self) -> str:
        """
        Search for the earliest backup of the autosave file.
        """
        files = os.listdir(self.autosave_path)
        if files:
            files = [Path(self.autosave_path, file).as_posix() for file in files]
            files = [file for file in files if os.path.isfile(file)]
            return min(files, key=os.path.getctime)

    def copies(self) -> int:
        """
        Returns number of copies in a folder
        """
        return len(os.listdir(self.autosave_path))

    def normal_path(self, path):
        return "\\".join(path.split("/")[:-1])

    def open_folder(self, path):
        if _OS_NAME == "Windows":
            os.system(r"explorer.exe " + self.normal_path(path))
        if _OS_NAME == "Linux":
            os.system(r"explorer.exe " + path)


class script(_folder):
    """
    subclass of the _folder class to make the code easier to understand.
    It is used for backup of autosaves to the scripts directory.
    """

    @classmethod
    def root_name(cls) -> str:
        """
        Returns the nuke script path
        """
        return nuke.root().name()

    @classmethod
    def button_open(cls):
        autosave = file.get_file()
        script_folder = script(
            path=file(autosave).parents, date=date(dt.datetime.now()).today
        )
        path = script_folder.autosave_path.as_posix()
        if _OS_NAME == "Windows":
            os.system(r"explorer.exe " + path.replace("/", "\\"))
        if _OS_NAME == "Linux":
            os.system(r"explorer.exe " + path)


class local(_folder):
    """
    subclass of the _folder class to make the code easier to understand.
    It is used for backup of autosaves to the local directory.
    """

    @property
    def shot_name(self) -> str:
        """Get shot name

        Returns:
            str: _description_
        """
        return script.root_name().split("/")[-1].split(".")[0]

    @classmethod
    def autosave_local(cls):
        """
        Returns the path to the local backup folder of autosave files.
        If the user does not specify a path, it returns the nuke home directory.
        """
        local_path = _NUKE_PREFERENCES["local_path"].value()
        if local_path:
            return _NUKE_PREFERENCES["local_path"].value()
        else:
            local_path = Path(Path().home(), "nuke", ".autosave").as_posix()
            return local_path

    @classmethod
    def button_open(cls):
        path = local.autosave_local()
        if ".autosave" not in path:
            path = Path(path, ".autosave").as_posix()
        if _OS_NAME == "Windows":
            os.system(r"explorer.exe " + path.replace("/", "\\"))
        if _OS_NAME == "Linux":
            os.system(r"explorer.exe " + path)


class save:

    def rename(self, file: str, name: str) -> None:
        """Renames the copied autosave to the backup folder

        Args:
            file (str): path to the copied file
            name (str): path with file name with time
        """
        os.rename(file, name)

    def copy(self, src: str, dst: str) -> None:
        """Сopying an autosave file from the script directory

        Args:
            src (str): path to the autosave file
            dst (str): path to the autosave dir
        """
        shutil.copy(src, dst)

    def get_checkpoint(self):

        return _NUKE_PREFERENCES["checkpoint_time"].value()

    def validation(self):
        checkpoint_string = self.get_checkpoint()
        checkpoint_time = date.str2time(checkpoint_string, "%Y-%m-%d %H:%M:%S")
        delta = dt.datetime.now() - checkpoint_time
        if file.exists_file():
            if int(delta.total_seconds() / 60) >= int(
                _NUKE_PREFERENCES["save_time"].value()
            ):
                return True
            else:
                return False
        else:
            return False


class preferences:

    @property
    def NUKE_PREFERENCES(self):
        return nuke.toNode("preferences")

    @property
    def as_status(self):
        """Autosave status check

        Returns:
            bool: return True or False
        """
        return _NUKE_PREFERENCES["enable_autosave"].value()

    @as_status.setter
    def as_status(self, value: bool):
        _NUKE_PREFERENCES["enable_autosave"].setValue(value)

    @property
    def local_value(self):
        return _NUKE_PREFERENCES["local_path"].value()

    @property
    def toggle_local(self):
        return _NUKE_PREFERENCES["copy_local"].value()

    @toggle_local.setter
    def toggle_local(self, value: bool):
        _NUKE_PREFERENCES["copy_local"].setValue(value)

    @property
    def num_copies(self):
        return _NUKE_PREFERENCES["number_copies"].value()

    @property
    def copy_local(self):
        return _NUKE_PREFERENCES["copy_local"].value()

    def set_local_path(self, value: str):
        _NUKE_PREFERENCES["local_path"].setValue(value)

    def set_checkpoint(self) -> None:
        _NUKE_PREFERENCES["checkpoint_time"].setValue(date.get_time())

    def add_to_preferences(
        self, knob_object: object, value=None, disable=None
    ) -> object:
        if knob_object.name() not in _NUKE_PREFERENCES.knobs().keys():
            _NUKE_PREFERENCES.addKnob(knob_object)
            if value is not None:
                _NUKE_PREFERENCES.knob(knob_object.name()).setValue(value)
            if disable:
                _NUKE_PREFERENCES.knob(knob_object.name()).setEnabled(False)
            self.save_preference_file()
        return _NUKE_PREFERENCES.knob(knob_object.name())

    def save_preference_file(self) -> None:
        nuke_folder = _folder._local_folder()
        pref_file = Path(
            nuke_folder,
            f"preferences{nuke.NUKE_VERSION_MAJOR}.{nuke.NUKE_VERSION_MINOR}.nk",
        )
        custom_preferences = _NUKE_PREFERENCES.writeKnobs(
            nuke.WRITE_USER_KNOB_DEFS
            | nuke.WRITE_NON_DEFAULT_ONLY
            | nuke.TO_SCRIPT
            | nuke.TO_VALUE
        ).replace("\n", "\n  ")
        code = "Preferences {\n inputs 0\n name Preferences%s\n}" % custom_preferences

        open_pref_file = open(pref_file, "w")
        open_pref_file.write(code)
        open_pref_file.close()

    def add_knobs(self) -> None:
        self.add_to_preferences(nuke.Tab_Knob("save_advanced", "aTimeBackup"))
        self.add_to_preferences(nuke.Text_Knob("general_label", "<b>General</b>"))

        self.add_to_preferences(
            nuke.Boolean_Knob("enable_autosave", "Enable autosave"), value=True
        )
        button = self.add_to_preferences(
            nuke.PyScript_Knob(
                "script_folder",
                "Open Folder",
                "aTimeBackup.lib.autosavelib.script.button_open()",
            )
        )
        button.clearFlag(nuke.STARTLINE)

        self.add_to_preferences(
            nuke.String_Knob("checkpoint_time", "checkpoint time"), disable=True
        )

        self.add_to_preferences(nuke.Int_Knob("save_time", "time minutes"), value=15)
        self.add_to_preferences(
            nuke.Int_Knob("number_copies", "number of copies"), value=10
        )

        self.add_to_preferences(nuke.Text_Knob("local_group", "Local settings"))
        self.add_to_preferences(
            nuke.Boolean_Knob("copy_local", "Enable copy to local"), value=False
        )
        button = self.add_to_preferences(
            nuke.PyScript_Knob("local_folder", "Open Folder"),
            "aTimeBackup.lib.autosavelib.local.button_open()",
        )
        button.clearFlag(nuke.STARTLINE)

        self.add_to_preferences(
            nuke.File_Knob("local_path", "local path backup"),
            value=Path(Path().home(), ".nuke").as_posix(),
        )
