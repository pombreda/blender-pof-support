#-------------------------------------------------------------------------------
# Name:        BSP Examiner
# Purpose:     Examine BSP data structs in POF files
#
# Author:      Christopher Koch
#
# Created:     17/01/2013
# Copyright:   (c) Christopher Koch 2013
# Licence:     WTFPL latest version
#-------------------------------------------------------------------------------

import os
import cmd
from volition import *

##class TextMenu:
##    """Base class for a text menu."""
##    _funct_dict = dict()
##    _disp_dict = dict()
##    def add_option(self, i, disp, funct):
##        """Adds option i, with display text disp,
##        that will perform function funct."""
##        self._funct_dict[i] = funct
##        self._disp_dict[i] = disp
##
##    def remove_option(self, i):
##        """Removes option i from the menu."""
##        try:
##            del self._funct_dict[i]
##            del self._disp_dict[i]
##        except KeyError:
##            pass
##
##    def display(self):
##        """Displays the menu and waits for input."""
##        disp_dict = self._disp_dict
##        for k, v in disp_dict.items():
##            print("{}: {}".format(k, v))
##        cmd = input("? ")
##        try:
##            self._funct_dict[cmd]()
##        except KeyError:
##            print("Bad command.")
##            self.display()
##
##class FileInput:
##    """Base class for file input prompt."""
##    def __init__(self, file_type=None):
##        self._file_type = file_type
##
##    def display(self, directory=None, flags='rb'):
##        file_type = self._file_type
##        if directory is None:
##            directory = os.getcwd()
##        else:
##            os.chdir(directory)
##        sep = os.sep
##        cur_dir = os.listdir(os.getcwd())
##        folders = list()
##        files = list()
##        # get files and folders so we can order them
##        for n in cur_dir:
##            full_name = sep.join([directory, n])
##            if os.path.isfile(full_name):
##                # filter file extensions
##                if file_type is None:
##                    files.append(n)
##                elif n.endswith(file_type):
##                    files.append(n)
##            if os.path.isdir(full_name):
##                folders.append(n)
##        folders.sort()
##        folders.insert(0, "..")
##        folders_idx = set()
##        files.sort()
##        files_idx = set()
##        cur_dir = folders + files
##        # display the current directory
##        i = 0
##        print(os.getcwd())
##        for n in folders:
##            print("{}: {}{}".format(i, n, sep))
##            folders_idx.add(i)
##            i += 1
##        for n in files:
##            print("{}: {}".format(i, n))
##            files_idx.add(i)
##            i += 1
##        folders = dict(zip(folders_idx, folders))
##        files = dict(zip(files_idx, files))
##        cmd = int(input("? "))
##        if cmd > i:
##            print("Bad command.")
##            self.display(directory)
##            return
##        if cmd == 0:
##            self.display("..")
##        elif cmd in folders_idx:
##            self.display(folders[cmd])
##        elif cmd in files_idx:
##            return open(files[cmd], flags)
##
##pof_input = FileInput(".pof")
##vp_input = FileInput(".vp")
##pof_file = pof_input.display()

class BSPShell(cmd.Cmd):
    intro = "POF file BSP tree examiner.  Type help of ? to list commands.\n"
    prompt = "<BSP> "
    file = None

    def do_read(self, arg):
        """Read a POF file: read herc.pof"""
