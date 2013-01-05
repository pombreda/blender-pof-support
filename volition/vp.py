# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

## VP module
## Copyright (c) 2012 by Christopher Koch

"""This module contains classes and methods for handling "Volition Package" (VP) files."""

## No guarantees about pep8 compliance

import time
import logging
from bintools import *
from . import VolitionError, FileFormatError

logging.basicConfig(filename="vp.log", level=logging.DEBUG)

class FileNotFoundError(VolitionError):
    def __init__(self, path, msg):
        self.path = path
        self.msg = msg
        
    def __str__(self):
        return "File not found: {}, {}.".format(self.path, self.msg)

class VolitionPackageFile:
    def __init__(self, vp_file):
        logging.info("Creating a VolitionPackageFile object.")
        vp_file_id = vp_file.read(4)
        logging.debug("File ID {}".format(vp_file_id))
        if vp_file_id != b"VPVP":
            raise FileFormatError(vp_file, "Not a VP file.")
            
        vp_file_version = unpack_int(vp_file.read(4))
        logging.debug("File spec version {}".format(vp_file_version))
        if vp_file_version > 2:
            raise FileFormatError(vp_file, "VP spec version greater than 2.")
            
        vp_diroffset = unpack_int(vp_file.read(4))
        logging.debug("diroffset {}".format(vp_diroffset))
        vp_num_files = unpack_int(vp_file.read(4))
        logging.info("VP contains {} dir entries".format(vp_num_files))
        
        vp_file_directory = Folder(b"root")
        parent_directory = vp_file_directory
        
        vp_file.seek(vp_diroffset)
        
        logging.info("Reading VP file")
        for i in range(vp_num_files):
            this_file_offset = unpack_int(vp_file.read(4))
            this_file_size = unpack_int(vp_file.read(4))
            this_file_name_long = vp_file.read(32)
            this_file_name = this_file_name_long.rstrip(b'\0')
            this_file_timestamp = unpack_int(vp_file.read(4))
            vp_dir_location = vp_file.tell()
            
            if not this_file_offset or not this_file_size or not this_file_timestamp:
                # direntry is either folder or backdir
                
                if this_file_name != b"..":     # folder
                    logging.debug("Folder {}".format(this_file_name))
                    this_node = Folder(this_file_name, parent_directory)
                    parent_directory.contents.add(this_node)
                    parent_directory = this_node
                else:                           # backdir
                    logging.debug("Backdir")
                    this_node = parent_directory
                    parent_directory = this_node.parent
            else:
                # direntry is a file
                
                logging.debug("File {}".format(this_file_name))
                vp_file.seek(this_file_offset)
                this_file_data = vp_file.read(this_file_size)
                this_node = File(this_file_name, this_file_data, this_file_timestamp, parent_directory)
                parent_directory.contents.add(this_node)
                vp_file.seek(vp_dir_location)
                
        logging.debug("Last file {}".format(this_node))
                
        self.vp_file_directory = vp_file_directory
        
    def get_file(self, path, sep='/'):
        parent_directory = self.vp_file_directory
        split_path = path.split(sep)
        logging.info("Retrieving file {}".format(path))
        logging.debug("Split path is {}".format(split_path))
        cur_node = parent_directory.contents
        logging.debug("cur_node at begin is {}".format(cur_node))
        
        for i, cur_dir in enumerate(split_path):
            for dir in cur_node:
                if dir.name == split_path[i]:
                    logging.debug("Found match. cur_node is {}".format(dir))
                    parent_directory = dir
                    cur_node = dir.contents
                    
        return parent_directory
        
    def remove_file(self, path, sep='/'):
        ## This is kind of hacked together - fix it!
        parent_directory = self.vp_file_directory
        split_path = path.split(sep)
        logging.info("Removing file {}".format(path))
        logging.debug("Split path is {}".format(split_path))
        cur_node = parent_directory.contents
        logging.debug("cur_node at begin is {}".format(cur_node))
        path_depth = len(split_path) - 1
        
        for i, cur_dir in enumerate(split_path):
            for dir in cur_node:
                if dir.name == split_path[i]:
                    logging.debug("Found match. cur_node is {}".format(dir))
                    parents_parent = parent_directory
                    parent_directory = dir
                    cur_node = dir.contents
                    
        if parent_directory.name == split_path[path_depth]:
            parents_parent.contents.remove(parent_directory)
        else:
            raise FileNotFoundError(path, " does not exist")
            
        return True
    # def set_file(self, path, file_data, sep='/'):
        # vp_file_directory = self.vp_file
        # split_path = path.split(sep)
        # timestamp = int(time.clock())
        # prev_dir = vp_file_directory
        
        # for i, dir in enumerate(split_path, 1):
            # try:
                # this_dir = prev_dir[dir]
                # prev_dir = this_dir
            # except KeyError:
                # if i != len(split_path):
                    # prev_dir[dir] = dict()    # path doesn't exist - create it
                    # this_dir = prev_dir[dir]
                    # prev_dir = this_dir
                # else:                         # end of path, create file
                    # prev_dir[dir] = (file_data, timestamp)
                    
    # def make_vp_file(self):
        # vp_file_id = b"VPVP"
        # vp_file_version = 2
        
        # vp_file_directory = self.vp_file
        
        # result = self._recurse_thru_directory(vp_file_directory)
        # vp_file_files = b"".join(result[0])
        # vp_file_index = b"".join(result[1])
        
        # vp_file_diroffset = result[2]
        # vp_file_num_files = len(result[1])
        # vp_file_head = b"".join([vp_file_id,
                                 # pack_int(vp_file_version),
                                 # pack_int(vp_file_diroffset),
                                 # pack_int(vp_file_num_files)])
        
        # vp_file = b"".join([vp_file_head, vp_file_files, vp_file_index])
        # return vp_file
        
    # def _recurse_thru_directory(self, vp_file_directory, cur_files=False, cur_index=False, cur_offset=16):
        # if not cur_index:
            # cur_index = list()
            
        # if not cur_files:
            # cur_files = list()
            
        # for k, v in vp_file_directory:
            
            # if isinstance(v, dict):
                # # entry is a folder
                # this_entry_offset = 0
                # this_entry_size = 0
                # this_entry_name = k
                # this_entry_timestamp = 0
                # cur_index.append("".join([pack_int(this_entry_offset),
                                          # pack_int(this_entry_size),
                                          # this_entry_name.ljust(32, b'\0'),
                                          # pack_int(this_entry_timestamp)]))
                # t = self._recurse_thru_directory(v, cur_files, cur_index, cur_offset)
                # cur_offset = t[2]
            # else:
                # # entry is a file
                # this_entry_offset = cur_offset
                # this_entry_size = len(v[0])
                # this_entry_name = k
                # this_entry_timestamp = v[1]
                # cur_files.append(v[0])
                # cur_offset += this_entry_size
                # cur_index.append("".join([pack_int(this_entry_offset),
                                  # pack_int(this_entry_size),
                                  # this_entry_name.ljust(32, b'\0'),
                                  # pack_int(this_entry_timestamp)]))
                                  
        # # done with dir, make backdir
        # this_entry_offset = 0
        # this_entry_size = 0
        # this_entry_name = b".."
        # this_entry_timestamp = 0
        # cur_index.append("".join([pack_int(this_entry_offset),
                                  # pack_int(this_entry_size),
                                  # this_entry_name.ljust(32, b'\0'),
                                  # pack_int(this_entry_timestamp)]))
                
        # return (cur_files, cur_index, cur_offset)
        
class Folder:
    def __init__(self, name, parent="", contents=None):
        self.name = name.decode().lower()
        if contents is not None:
            self.contents = set(contents)
        else:
            self.contents = set()
        self.parent = parent
        self.parent_name = str(parent)
        
    def __eq__(self, other):
        if self.name == other.name and self.parent == other.parent:
            return True
        else:
            return False
            
    def __hash__(self):
        return hash(self.name)
        
    def __repr__(self):
        return "/".join([self.parent_name, self.name])
        
class File:
    def __init__(self, name, contents, timestamp=False, parent=""):
        self.name = name.decode().lower()
        self.contents = contents
        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = int(time.clock())
        self.parent = parent
        self.parent_name = str(parent)
            
    def __len__(self):
        return len(contents)
        
    def __eq__(self, other):
        if self.name == other.name and self.parent == other.parent:
            return True
        else:
            return False
            
    def __hash__(self):
        return hash(self.name)
        
    def __repr__(self):
        return "/".join([self.parent_name, self.name])