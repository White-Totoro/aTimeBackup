import datetime as dt
import os
from importlib import reload
from pathlib import Path

import nuke

from lib.autosavelib import date, file, local, preferences, save, script

settings = preferences()
local_folder = None


def root_validation():
    if script.root_name() != "Root":
        return True
    else:
        print("the script has not been saved")
        return False


def timer():
    if root_validation():
        if save().validation() and settings.as_status:
            print("start backup, and script save")
            # create log file
            nuke.addOnScriptSave(run_save)
            nuke.scriptSave()
            nuke.removeOnScriptSave(run_save)


def run_save():

    FILE = settings.NUKE_PREFERENCES["AutoSaveName"].evaluate()
    DATE = dt.datetime.now()

    as_file = file(FILE)
    as_date = date(DATE)
    as_save = save()

    script_folder = script(path=as_file.parents, date=as_date.today)
    if settings.toggle_local:
        local_folder = local(path=settings.local_value, date=as_date.today)

    def _save_file(path_object: object, local=None):
        settings.set_checkpoint()
        path_to_save = path_object.autosave_path
        print("SCRIPT_PATH_TO_SAVE: %s" % path_to_save)
        if local is not None:
            path_to_save = Path(settings.local_value, ".autosave", as_date.today).as_posix()
            print("LOCAL_PATH_TO_SAVE: %s" % path_to_save)
        path_object.exists(path_to_save)
        _name = as_file.name
        old_name = as_file.add_ext(_name)
        time_name = as_file.add_time_to_name(_name, as_date.name_time())
        save_file_path = as_file.merge(path_to_save, old_name)
        save_file_with_time = as_file.merge(path_to_save, as_file.add_ext(time_name))
        as_save.copy(FILE, save_file_path)
        as_save.rename(save_file_path, save_file_with_time)
        if path_object.copies() > int(settings.num_copies):
            early_file = path_object.find_early_file()
            print("EARLY_FILE", early_file)
            os.remove(early_file)

    if file.exists_file():
        _save_file(script_folder)
        if settings.copy_local:
            _save_file(local_folder, local=True)


def script_enable():
    settings.as_status = True


def script_disable():
    settings.as_status = False


def local_enable():
    settings.toggle_local = True


def local_disable():
    settings.toggle_local = False


def script_open_folder():
    autosave = file.get_file()
    as_file = file(autosave)
    script_folder = script(path=as_file.parents, date=date(dt.datetime.now()).today)
    path = script_folder.autosave_path
    script_folder.open_folder(path.as_posix())


def local_open_folder():
    local_path = local.autosave_local()
    if ".autosave" not in local_path:
        local_path = Path(local_path, ".autosave").as_posix()
    local_folder = local(path=local_path, date=date(dt.datetime.now()).today)
    local_folder.open_folder(local_path)


def add_edit_items():
    mode_list = ["Script", "Local"]
    func_list = ["Enable", "Disable", "Open folder"]
    edit_menu = nuke.menu("Nuke").findItem("Edit")

    edit_menu.addCommand("-", "", "")
    for mode in mode_list:
        for func in func_list:
            edit_menu.addCommand(
                f"aTimeBackup/{mode}/{func}",
                f"aTimeBackup.main.{mode.lower()}_{func.lower()}()",
            )
            if func == "Open folder":
                item = edit_menu.findItem(f"aTimeBackup/{mode}/{func}")
                item.setScript(f"aTimeBackup.main.{mode.lower()}_open_folder()")


def init():
    settings.add_knobs()
    settings.set_checkpoint()


def install():
    add_edit_items()
    nuke.addUpdateUI(timer)
