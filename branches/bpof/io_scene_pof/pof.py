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

## POF module
## Copyright (c) 2012 by Christopher Koch

"""This module contains classes and methods for handling "Parallax Object Format" (POF) files, including geometry helper classes for mesh data."""

## No guarantees about pep8 compliance


from math import fsum, sqrt
from .bintools import *
import logging


## Exceptions ##


class VolitionError(Exception):
    """Base class for exceptions in this module."""
    pass
    

class FileFormatError(VolitionError):
    """Exception raised for invalid filetype errors.

    Attributes:
        path -- the filepath of the invalid file
        msg  -- a message"""
    def __init__(self, path, msg):
        self.path = path
        self.msg = msg
        
    def __str__(self):
        return "{}, {}.".format(self.msg, self.path)


class InvalidChunkError(VolitionError):
    """Exception raised for invalid chunk data.

    Attributes:
        chunk -- the chunk with invalid data
        msg -- a message"""
    def __init__(self, chunk, msg):
        self.chunk = repr(chunk)
        self.msg = msg

    def __str__(self):
        return "Invalid chunk data: {}, {}.".format(self.msg, self.chunk)


class InvalidBSPError(VolitionError):
    """Exception raised for invalid BSP data.

    Attributes:
        block -- the BSP block with the invalid data
        msg -- a message"""
    def __init__(self, block, msg):
        self.block = block
        self.msg = msg

    def __str__(self):
        return "Invalid BSP data: {}, {}.".format(self.msg, self.block)


class GeometryError(VolitionError):
    """Exception raised for invalid geometry of some sort.

    Attributes:
        coords -- coordinates of the geometry error
        msg -- a message"""
    def __init__(self, coords, msg):
        self.coords = coords
        self.msg = msg

    def __str__(self):
        return "Bad geometry: {}, {}.".format(self.msg, self.coords)


class VertListError(VolitionError):
    """Exception raised for an invalid vertex list.

    Attributes:
        vert -- the vertex object with the invalid data
        msg -- a message"""
    def __init__(self, vert, msg):
        self.vert = vert
        self.msg = msg

    def __str__(self):
        return "Bad vertex: {}, {}.".format(self.msg, self.vert)


class FaceListError(GeometryError):
    """Exception raised for an invalid face list.

    Attributes:
        face -- the face object with the invalid data
        msg -- a message"""
    def __init__(self, face, msg):
        self.face = face
        self.msg = msg

    def __str__(self):
        return "Bad face: {}, {}.".format(self.msg, self.face)


## Helper types ##


def vector(x = None, y = None, z = None):
    """A sequence of floats.  Returns a tuple.

    Attributes:
        x=0 -- float -- x-axis point
        y=0 -- float -- y-axis point
        z=0 -- float -- z-axis point"""
    if x is None or y is None or z is None:
        return False
    else:
        return (float(x), float(y), float(z))


def vdist(a, b):
    """
    Get 3d distance between two vectors
    """
    x1 = a[0]
    x2 = b[0]
    y1 = a[1]
    y2 = b[1]
    z1 = a[2]
    z2 = b[2]
    return sqrt((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2)


class Mesh:
    """
    A collection of lists
    
    verts - a list of vectors representing vertex coords (assigned)
    faces - a list of 3-tuples representing vertex indices (assigned)
    fvnorms - list of 3-tuples representing vertex normal indices (export only)
    fnorms - a list of 3-tuples representing face normals (export only)
    vnorms - a list of 3-tuples of vectors representing vertex normals (assigned)
    num_norms - a list indicating the number of normals each vertex has (assigned, import only)
    edges - a dict where each key is a frozenset of two vectors representing
        vertex coords and where each value is bool, whether the edge is sharp (import only) (calc)
    fradii - a list of face radii (export only) (calc)
    centers - a list of face centers (export only) (assigned)
    tex_ids - a list of texture ids (assigned) == material id in Blender

    When using the edge split modifier in Blender, you basically get duplicate vertices,
    each with its own normal.  During export, we should determine if a vertex is already
    in the vertex list, and if it is, use its index instead of adding a new one.
    """
    def calc_sharp(self):
        """
        Calculate edges from face and normal lists

        Use during import
        """
        # Let's do this the easy way, sharp if edge includes vert with >1 norm
        # for each face
            # for each pair of verts in face
                # make a frozenset of the verts coords
                # for each vert in pair
                    # if vert has >1 norm
                        # edge is sharp
                    # else
                        # edge is not sharp
        faces = self.faces
        verts = self.verts
        num_norms = self.num_norms
        edges = dict()
        for f in faces:
            e1 = verts[f[0]], verts[f[1]]
            e2 = verts[f[1]], verts[f[2]]
            e3 = verts[f[2]], verts[f[0]]
            e1 = frozenset(e1)
            e2 = frozenset(e2)
            e3 = frozenset(e3)
            if num_norms[f[0]] == 1:
                # if this edge is already accounted for,
                # either it will already be False or True
                # takes priority
                if e1 not in edges.keys():
                    edges[e1] = False
                if e3 not in edges.keys():
                    edges[e3] = False
            else:
                edges[e1] = True
                edges[e2] = True
            if num_norms[f[1]] == 1:
                if e1 not in edges.keys():
                    edges[e1] = False
                if e2 not in edges.keys():
                    edges[e2] = False
            else:
                edges[e1] = True
                edges[e2] = True
            if num_norms[f[2]] == 1:
                if e2 not in edges.keys():
                    edges[e2] = False
                if e3 not in edges.keys():
                    edges[e3] = False
            else:
                edges[e2] = True
                edges[e3] = True

        self.edges = edges

    def calc_fradii(self):
        """
        Calculate fradii
        
        Use during export
        """
        # where a, b, c are the length of each edge:
        # r = abc / sqrt(2aabb + 2bbcc + 2ccaa - a**4 - b**4 - c**4)
        faces = self.faces
        verts = self.verts
        fradii = list()
        for f in faces:
            a = vdist(verts[f[0]], verts[f[1]])
            b = vdist(verts[f[1]], verts[f[2]])
            c = vdist(verts[f[2]], verts[f[0]])
            a2 = a**2
            b2 = b**2
            c2 = c**2
            a4 = a**4
            b4 = b**4
            c4 = c**4
            num = a * b * c
            denom = sqrt(2 * a2 * b2 + 2 * b2 * c2 + 2 * c2 * a2 - a4 - b4 - c4)
            fradii.append(num/denom)

    def flip_yz(self):
        """
        Switch Y axis with Z axis
        """
        verts = self.verts
        new_verts = list()
        for v in verts:
            # no fancy slicing here, v is a tuple
            x = v[0]
            y = v[1]
            z = v[2]
            v = (x, z, y)
            new_verts.append(v)
        self.verts = new_verts

    def flip_v(self):
        """
        Flip V axis of UV coords
        """
        uv = self.uv
        new_uv = list()
        for i, face in enumerate(uv):
            new_uv.append(list())
            for vert in face:
                u = vert[0]
                v = vert[1] * -1
                new_uv[i].append([u, v])
        self.uv = new_uv


## POF helpers ##


class PolyModel:
    """Container class for a collection of POFChunks"""
    # I want this class to contain methods for getting and
    # setting various objects (e.g. paths) once we get classes
    # for those objects.
    def __init__(self, chunks, pof_ver):
        self.pof_ver = pof_ver
        self.chunks = dict()
        self.submodels = dict()
        for chunk in chunks:
            if chunk.CHUNK_ID == b'HDR2' or chunk.CHUNK_ID == b'OHDR':
                self.header = chunk
            if chunk.CHUNK_ID == b'OBJ2' or chunk.CHUNK_ID == b'SOBJ':
                print(chunk.model_id)
                self.submodels[chunk.model_id] = chunk
            elif chunk.CHUNK_ID == b' EYE' or chunk.CHUNK_ID == b'EYE ':
                self.chunks['EYE'] = chunk
            else:
                # There should only be one of each type of chunk
                # other than submodels
                chunk_id = chunk.CHUNK_ID.decode()
                self.chunks[chunk_id] = chunk

    def get_chunk_list(self):
        chunk_list = [None for i in range(16)]
        for chunk in self.chunks.keys():
            chunk_idx = chunk_order[chunk]
            chunk_list[chunk_idx] = self.chunks[chunk]
        while None in chunk_list:
            chunk_list.remove(None)
        i = 2
        for chunk in self.submodels.values():
            chunk_list.insert(i, chunk)
            i += 1
        return chunk_list

    def verify_pof(self, pof_ver=None):
        if pof_ver is None:
            pof_ver = self.pof_ver
        else:
            self.pof_ver = pof_ver
        chunks = self.chunks
        for chunk in chunks.values():
            chunk.pof_ver = pof_ver
        submodels = self.submodels
        for chunk in submodels.values():
            chunk.pof_ver = pof_ver

        # verify header

        header = self.header

        if pof_ver >= 2116 and header.CHUNK_ID == b'OHDR':
            header.CHUNK_ID = b'HDR2'
            chunks["HDR2"] = header
            del chunks["OHDR"]
        elif pof_ver < 2116 and header.CHUNK_ID == b'HDR2':
            header.CHUNK_ID = b'OHDR'
            chunks["OHDR"] = header
            del chunks["HDR2"]

        if pof_ver >= 2009 and header.pof_ver < 2009:
            # convert volume mass to area mass
            vol_mass = header.mass
            area_mass = 4.65 * (vol_mass ** 2 / 3)
            header.mass = area_mass
            for i in header.inertia_tensor:
                for j in i:
                    j *= vol_mass / area_mass
        elif pof_ver < 2009 and header.pof_ver >= 2009:
            # convert area mass to volume mass
            area_mass = header.mass
            vol_mass = abs(2 * sqrt(5 / 31) * sqrt(area_mass))
            header.mass = vol_mass
            for i in header.inertia_tensor:
                for j in i:
                    j *= area_mass / vol_mass

        header.num_subobjects = len(submodels)
        sobj_debris = set(header.sobj_debris)
        sobj_details = set(header.sobj_detail_levels)
        if not sobj_debris.isdisjoint(sobj_details):
            raise InvalidChunkError(header, "Set of debris submodels intersects set of LOD submodels")
        for i in sobj_debris:
            if i >= header.num_subobjects:
                raise InvalidChunkError(header, "Debris submodel does not exist, {}".format(i))
        for i in sobj_details:
            if i >= header.num_subobjects:
                raise InvalidChunkError(header, "Detail level submodel does not exist, {}".format(i))

        # verify submodels

        sobj_max_x = set()
        sobj_max_y = set()
        sobj_max_z = set()
        sobj_min_x = set()
        sobj_min_y = set()
        sobj_min_z = set()
        delta = set()
        model_ids = set()
        for model in submodels.values():
            if pof_ver >= 2116 and model.CHUNK_ID == b'SOBJ':
                model.CHUNK_ID = b'OBJ2'
            elif pof_ver < 2116 and model.CHUNK_ID == b'OBJ2':
                model.CHUNK_ID = b'SOBJ'

            if model.model_id in model_ids:
                raise InvalidChunkError(model, "Duplicate model id")
            else:
                model_ids.add(model.model_id)

            if model.parent_id >= header.num_subobjects:
                raise InvalidChunkError(model, "Model parent does not exist")
            delta.add(model.max[0] - model.center[0])
            delta.add(model.max[1] - model.center[1])
            delta.add(model.max[2] - model.center[2])
            delta.add(model.center[0] - model.min[0])
            delta.add(model.center[1] - model.min[1])
            delta.add(model.center[2] - model.min[2])
            sobj_max_x.add(model.max[0])
            sobj_max_y.add(model.max[1])
            sobj_max_z.add(model.max[2])
            sobj_min_x.add(model.min[0])
            sobj_min_y.add(model.min[1])
            sobj_min_z.add(model.min[2])
        header.max_radius = max(delta)
        max_x = max(sobj_max_x)
        max_y = max(sobj_max_y)
        max_z = max(sobj_max_z)
        min_x = min(sobj_min_x)
        min_y = min(sobj_min_y)
        min_z = min(sobj_min_z)
        header.max_bounding = vector(max_x, max_y, max_z)
        header.min_bounding = vector(max_x, max_y, max_z)

        # verify autocenter point

        if "ACEN" in chunks and pof_ver < 2116:
            del chunks["ACEN"]
        elif "ACEN" not in chunks and pof_ver >= 2116:
            acen = CenterChunk()
            acen.co = vector(0,0,0)
            chunks["ACEN"] = acen

        # verify shield collision tree

        if "SHLD" in chunks:
            if "SLDC" in chunks and pof_ver < 2117:
                del chunks["SLDC"]
            elif "SLDC" not in chunks and pof_ver >= 2117:
                sldc = TreeChunk()
                sldc.make_shield_collision_tree(chunks["SHLD"])
                chunks["SLDC"] = sldc
        elif "SLDC" in chunks:
            del chunks["SLDC"]

        # verify paths

        if "PATH" in chunks:
            path = chunks["PATH"]
            for p in path.path_parents:
                if not self.get_submodel_by_name(p) and p != b'':
                    raise InvalidChunkError(path, "Path parent not found, {}".format(p))
            for i, p in enumerate(path.turret_sobj_num):
                for v in p:
                    for t in v:
                        if (t in header.sobj_debris or
                            t in header.sobj_detail_levels or
                            t >= header.num_subobjects):
                            raise InvalidChunkError(path, "Submodel does not exist or is not a turret, path {}".format(i))

        # verify gpnt/mpnt

        if "GPNT" in chunks:
            if len(chunks["GPNT"].gun_points) > 3:
                raise InvalidChunkError(chunks["GPNT"], "Primary weapons has more than three slots")
        if "MPNT" in chunks:
            if len(chunks["MPNT"].gun_points) > 2:
                raise InvalidChunkError(chunks["MPNT"], "Secondary weapons has more than two slots")

        # verify tgun/tmis

        if "TGUN" in chunks:
            for j, i in enumerate(chunks["TGUN"].barrel_sobj):
                if (i > header.num_subobjects or
                    i in header.sobj_debris or
                    i in header.sobj_detail_levels):
                    raise InvalidChunkError(chunks["TGUN"], "Barrel submodel does not exist or is not a turret, turret {}".format(j))
            for j, i in enumerate(chunk["TGUN"].base_sobj):
                if (i > header.num_subobjects or
                    i in header.sobj_debris or
                    i in header.sobj_detail_levels):
                    raise InvalidChunkError(chunks["TGUN"], "Base submodel does not exist or is not a turret, turret {}".format(j))
        if "TMIS" in chunks:
            for j, i in enumerate(chunks["TMIS"].barrel_sobj):
                if (i > header.num_subobjects or
                    i in header.sobj_debris or
                    i in header.sobj_detail_levels):
                    raise InvalidChunkError(chunks["TMIS"], "Barrel submodel does not exist or is not a turret, turret {}".format(j))
            for j, i in enumerate(chunk["TMIS"].base_sobj):
                if (i > header.num_subobjects or
                    i in header.sobj_debris or
                    i in header.sobj_detail_levels):
                    raise InvalidChunkError(chunks["TMIS"], "Base submodel does not exist or is not a turret, turret {}".format(j))

        # verify docks

        if "DOCK" in chunks:
            for i, d in enumerate(chunks["DOCK"].path_id):
                for p in d:
                    if p >= len(chunks["PATH"].path_names):
                        raise InvalidChunkError(chunks["DOCK"], "Path does not exist for dock {}".format(i))

        # verify insignia

        if "INSG" in chunks and pof_ver >= 2116:
            for j, i in enumerate(chunks["INSG"].insig_detail_level):
                if i not in header.sobj_detail_levels:
                    raise InvalidChunkError(chunks["INSG"], "LOD submodel not found for insignia {}".format(j))
        elif "INSG" in chunks and pof_ver < 2116:
            del chunks["INSG"]

        # verify glowpoints

        if "GLOW" in chunks and pof_ver >= 2117:
            for j, i in enumerate(chunks["GLOW"].parent_id):
                if i >= header.num_subobjects:
                    raise InvalidChunkError(chunks["GLOW"], "Parent submodel not found for glow bank {}".format(j))
        if "GLOW" in chunks and pof_ver < 2117:
            del chunks["GLOW"]

        self.chunks = chunks
        self.submodels = submodels

    def get_submodel_by_name(self, name):
        name = bytes(name, "utf-8")

        for model in self.submodels.values():
            if model.model_id == name:
                return model
        else:
            return None


class POFChunk:
    """Base class for all POF chunks.  Calling len() on a chunk will return the estimated size of the packed binary chunk, minus chunk header."""
    CHUNK_ID = b"PSPO"
    def __init__(self, pof_ver=2117, chunk_id=b'PSPO'):
        self.pof_ver = pof_ver

    def __len__(self):
        return 0

    def __repr__(self):
        return "<POF chunk with ID {} and size {}>".format(self.CHUNK_ID, len(self))


## POF chunks and BSP blocks ##


class HeaderChunk(POFChunk):
    def __init__(self, pof_ver=2117, chunk_id=b'PSPO'):
        self.pof_ver = pof_ver
        if pof_ver >= 2116:
            self.CHUNK_ID = b'HDR2'
        else:
            self.CHUNK_ID = b'OHDR'

    def read_chunk(self, bin_data):
        if self.pof_ver >= 2116:        # FreeSpace 2
            self.max_radius = unpack_float(bin_data.read(4))
            self.obj_flags = unpack_int(bin_data.read(4))
            self.num_subobjects = unpack_int(bin_data.read(4))

        else:                            # FreeSpace 1
            self.num_subobjects = unpack_int(bin_data.read(4))
            self.max_radius = unpack_float(bin_data.read(4))
            self.obj_flags = unpack_int(bin_data.read(4))

        self.min_bounding = unpack_vector(bin_data.read(12))
        self.max_bounding = unpack_vector(bin_data.read(12))

        self.num_detail_levels = unpack_int(bin_data.read(4))
        sobj_detail_levels = list()
        for i in range(self.num_detail_levels):
            sobj_detail_levels.append(unpack_int(bin_data.read(4)))
        self.sobj_detail_levels = sobj_detail_levels

        self.num_debris = unpack_int(bin_data.read(4))
        sobj_debris = list()
        for i in range(self.num_debris):
            sobj_debris.append(unpack_int(bin_data.read(4)))
        self.sobj_debris = sobj_debris

        if self.pof_ver >= 1903:
            self.mass = unpack_float(bin_data.read(4))
            self.mass_center = unpack_vector(bin_data.read(12))
            self.inertia_tensor = unpack_vector(bin_data.read(36))

        if self.pof_ver >= 2014:
            num_cross_sections = unpack_int(bin_data.read(4))
            cross_section_depth = list()
            cross_section_radius = list()
            for i in range(num_cross_sections):
                cross_section_depth.append(unpack_float(bin_data.read(4)))
                cross_section_radius.append(unpack_float(bin_data.read(4)))
            self.num_cross_sections = num_cross_sections
            self.cross_section_depth = cross_section_depth
            self.cross_section_radius = cross_section_radius

        if self.pof_ver >= 2007:
            num_lights = unpack_int(bin_data.read(4))
            light_location = list()
            light_type = list()
            for i in range(num_lights):
                light_location.append(unpack_vector(bin_data.read(12)))
                light_type.append(unpack_int(bin_data.read(4)))
            self.light_locations = light_location
            self.light_types = light_type

    def write_chunk(self):

        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        logging.debug("Writing header chunk with size {}...".format(length))

        if self.pof_ver >= 2116:
            chunk += pack_float(self.max_radius)
            chunk += pack_int(self.obj_flags)
            chunk += pack_int(self.num_subobjects)
        else:
            chunk += pack_int(self.num_subobjects)
            chunk+= pack_float(self.max_radius)
            chunk += pack_int(self.obj_flags)

        chunk += pack_float(self.min_bounding)
        chunk += pack_float(self.max_bounding)

        chunk += pack_int(self.num_detail_levels)
        chunk += pack_int(self.sobj_detail_levels)

        chunk += pack_int(self.num_debris)
        chunk += pack_int(self.sobj_debris)

        if self.pof_ver >= 1903:
            chunk += pack_float(self.mass)
            chunk += pack_float(self.mass_center)
            inertia_tensor = self.inertia_tensor
            for i in inertia_tensor:
                chunk += pack_float(i)

        if self.pof_ver >= 2014:
            cross_section_depth = self.cross_section_depth
            cross_section_radius = self.cross_section_radius
            num_cross_sections = len(cross_section_depth)
            chunk += pack_int(num_cross_sections)
            for i in range(num_cross_sections):
                chunk += pack_float(cross_section_depth[i])
                chunk += pack_float(cross_section_radius[i])

        if self.pof_ver >= 2007:
            light_locations = self.light_locations
            light_types = self.light_types
            num_lights = len(light_locations)
            chunk += pack_int(num_lights)
            for i in range(num_lights):
                chunk += pack_float(light_locations[i])
                chunk += pack_int(light_types[i])

        return chunk

    def __len__(self):
        chunk_length = 52        # Chunk Size
        try:
            if self.sobj_detail_levels:
                chunk_length += 4 * self.num_detail_levels
        except AttributeError:
            pass
        try:
            if self.sobj_debris:
                chunk_length += 4 * self.num_debris
        except AttributeError:
            pass
        try:
            if self.mass:
                chunk_length += 52
        except AttributeError:
            pass
        try:
            if self.cross_section_depth:
                chunk_length += 4 + len(self.cross_section_depth) * 8
        except AttributeError:
            chunk_length += 4
        try:
            if self.light_locations:
                chunk_length += 4 + len(self.light_locations) * 16
        except AttributeError:
            chunk_length += 4
        return chunk_length


class TextureChunk(POFChunk):
    CHUNK_ID = b'TXTR'
    def read_chunk(self, bin_data):
        num_textures = unpack_int(bin_data.read(4))
        textures = list()
        for i in range(num_textures):
            str_len = unpack_int(bin_data.read(4))
            textures.append(bin_data.read(str_len))
        self.textures = textures

    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        logging.debug("Writing texture chunk with size {}...".format(length))

        textures = self.textures

        chunk += pack_int(len(textures))

        for s in textures:
            chunk += pack_string(s)

        return chunk

    def __len__(self):
        try:
            chunk_length = 4
            textures = self.textures
            for s in textures:
                chunk_length += 4 + len(s)
            return chunk_length
        except AttributeError:
            return 0


class MiscChunk(POFChunk):
    CHUNK_ID = b'PINF'
    def read_chunk(self, bin_data):
        self.lines = bin_data.read().decode('UTF-8').split('\0')

    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        logging.debug("Writing PINF chunk with size {}...".format(length))

        chunk += bytes("\0".join(self.lines) + "\0")

        return chunk

    def __len__(self):
        try:
            lines = self.lines
            chunk_length = len(lines)
            for s in lines:
                chunk_length += len(s)

            return chunk_length
        except AttributeError:
            return 0


class PathChunk(POFChunk):
    CHUNK_ID = b'PATH'
    def read_chunk(self, bin_data):
        num_paths = unpack_int(bin_data.read(4))

        path_names = list()
        path_parents = list()
        num_verts = list()
        vert_list = list()
        vert_rad = list()
        vert_num_turrets = list()
        turret_sobj_num = list()

        for i in range(num_paths):
            str_len = unpack_int(bin_data.read(4))
            path_names.append(bin_data.read(str_len))

            str_len = unpack_int(bin_data.read(4))
            path_parents.append(bin_data.read(str_len))

            num_verts.append(unpack_int(bin_data.read(4)))

            vert_list.append(list())
            vert_rad.append(list())
            vert_num_turrets.append(list())
            turret_sobj_num.append(list())

            for j in range(num_verts[i]):
                vert_list[i].append(unpack_vector(bin_data.read(12)))
                vert_rad[i].append(unpack_float(bin_data.read(4)))
                vert_num_turrets[i].append(unpack_int(bin_data.read(4)))

                turret_sobj_num[i].append(list())

                for k in range(vert_num_turrets[i][j]):
                    turret_sobj_num[i][j].append(unpack_int(bin_data.read(4)))

        self.path_names = path_names
        self.path_parents = path_parents
        self.vert_list = vert_list
        self.vert_rad = vert_rad
        self.turret_sobj_num = turret_sobj_num

    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        logging.debug("Writing path chunk with size {}...".format(length))

        path_names = self.path_names
        path_parents = self.path_parents
        vert_list = self.vert_list
        vert_rad = self.vert_rad
        turret_sobj_num = self.turret_sobj_num
        num_paths = len(path_names)

        chunk += pack_int(num_paths)

        for i in range(num_paths):
            chunk += pack_int(len(path_names[i]))
            chunk += path_names[i]

            chunk += pack_int(len(path_parents[i]))
            chunk += path_parents[i]

            num_verts = len(vert_list[i])
            chunk += pack_int(num_verts)

            for j in range(num_verts):
                chunk += pack_float(vert_list[i][j])
                chunk += pack_float(vert_rad[i][j])

                num_turrets = len(turret_sobj_num[i][j])
                chunk += pack_int(num_turrets)

                for k in range(num_turrets):
                    chunk += pack_int(turret_sobj_num[i][j][k])

        return chunk

    def __len__(self):
        try:
            chunk_length = 4

            path_names = self.path_names
            path_parents = self.path_parents
            turret_sobj_num = self.turret_sobj_num
            vert_list = self.vert_list

            for i in range(len(path_names)):
                chunk_length += 4 + len(path_names[i])
                chunk_length += 4 + len(path_parents[i])
                chunk_length += 4

                for j in range(len(vert_list[i])):
                    chunk_length += 20
                    chunk_length += 4 * len(turret_sobj_num[i][j])

            return chunk_length
        except AttributeError:
            return 0


class SpecialChunk(POFChunk):
    CHUNK_ID = b'SPCL'
    def read_chunk(self, bin_data):
        num_special_points = unpack_int(bin_data.read(4))

        point_names = list()
        point_properties = list()
        points = list()
        point_radius = list()

        for i in range(num_special_points):
            str_len = unpack_int(bin_data.read(4))
            point_names.append(bin_data.read(str_len))

            str_len = unpack_int(bin_data.read(4))
            point_properties.append(bin_data.read(str_len))

            points.append(unpack_vector(bin_data.read(12)))
            point_radius.append(unpack_float(bin_data.read(4)))

        self.point_names = point_names
        self.point_properties = point_properties
        self.points = points
        self.point_radius = point_radius

    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        logging.debug("Writing special point chunk with size {}...".format(length))

        point_names = self.point_names
        point_properties = self.point_properties
        points = self.points
        point_radius = self.point_radius

        num_special_points = len(points)
        chunk += pack_int(num_special_points)

        for i in range(num_special_points):
            chunk += pack_string(point_names[i])
            chunk += pack_string(point_properties[i])
            chunk += pack_float(points[i])
            chunk += pack_float(point_radius[i])

        return chunk

    def __len__(self):
        try:
            chunk_length = 4

            point_names = self.point_names
            point_properties = self.point_properties

            for i in range(len(point_names)):
                chunk_length += 4 + len(point_names[i])
                chunk_length += 4 + len(point_properties[i])
                chunk_length += 16

            return chunk_length
        except AttributeError:
            return 0


class ShieldChunk(POFChunk):
    CHUNK_ID = b'SHLD'
    name = b"shield"    # needed for blender
    model_id = -1       # needed for blender
    def read_chunk(self, bin_data):
        num_verts = unpack_int(bin_data.read(4))

        vert_list = list()

        for i in range(num_verts):
            vert_list.append(unpack_vector(bin_data.read(12)))

        self.vert_list = vert_list

        num_faces = unpack_int(bin_data.read(4))

        face_normals = list()
        face_list = list()
        face_neighbors = list()

        for i in range(num_faces):
            face_normals.append(unpack_vector(bin_data.read(12)))
            face_list.append(unpack_int(bin_data.read(12)))
            face_neighbors.append(unpack_int(bin_data.read(12)))

        self.face_normals = face_normals
        self.face_list = face_list
        self.face_neighbors = face_neighbors

    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        logging.debug("Writing shield chunk with size {}...".format(length))

        vert_list = self.vert_list
        num_verts = len(vert_list)
        chunk += pack_int(num_verts)

        for i in range(num_verts):
            chunk += pack_float(vert_list[i])

        face_normals = self.face_normals
        face_list = self.face_list
        face_neighbors = self.face_neighbors

        num_faces = len(face_list)
        chunk += pack_int(num_faces)

        for i in range(num_faces):
            chunk += pack_float(face_normals[i])
            chunk += pack_int(face_list[i])
            chunk += pack_int(face_neighbors[i])

        return chunk

    def get_mesh(self):

        shld_mesh = Mesh()
        shld_mesh.verts = self.vert_list
        shld_mesh.faces = self.face_list
        return shld_mesh

    def set_mesh(self, m):

        self.num_verts = len(m.verts)
        self.vert_list = m.verts

        self.num_faces = len(m.faces)
        face_list = m.faces
        self.face_normals = m.fnorms
        
        # for getting neighbors, we could:
        # for each face
            # for each pair of verts
                # for each face
                    # if pair of verts in face, add neighbor

        face_neighbors = list()
        for i, f in enumerate(face_list):
            face_neighbors.append(list())
            e1 = {f[0], f[1]}
            e2 = {f[1], f[2]}
            e3 = {f[2], f[0]}
            for j, n in enumerate(face_list):
                v = set(n)
                if e1 < v or e2 < v or e3 < v:
                    face_neighbors[i].append(j)

        self.face_list = face_list
        self.face_neighbors = face_neighbors

    def __len__(self):
        try:
            chunk_length = 8

            chunk_length += 12 * len(self.vert_list)
            chunk_length += 36 * len(self.face_list)

            return chunk_length
        except AttributeError:
            return 0


class EyeChunk(POFChunk):
    CHUNK_ID = b" EYE"
    def read_chunk(self, bin_data):
        num_eyes = unpack_int(bin_data.read(4))
        sobj_num = list()
        eye_offset = list()
        eye_normal = list()

        for i in range(num_eyes):
            sobj_num.append(unpack_int(bin_data.read(4)))
            eye_offset.append(unpack_vector(bin_data.read(12)))
            eye_normal.append(unpack_vector(bin_data.read(12)))

        self.sobj_num = sobj_num
        self.eye_offset = eye_offset
        self.eye_normal = eye_normal

    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        logging.debug("Writing eye chunk with size {}...".format(length))

        sobj_num = self.sobj_num
        eye_offset = self.eye_offset
        eye_normal = self.eye_normal

        num_eyes = len(eye_normal)
        chunk += pack_int(num_eyes)

        for i in range(num_eyes):
            chunk += pack_int(sobj_num[i])
            chunk += pack_float(eye_offset[i])
            chunk += pack_float(eye_normal[i])

        return chunk

    def __len__(self):
        try:
            chunk_length = 4
            chunk_length += 28 * len(self.eye_normal)
            return chunk_length
        except AttributeError:
            return 0


class GunChunk(POFChunk):           # GPNT and MPNT
    def __init__(self, pof_ver=2117, chunk_id=b'GPNT'):
        self.pof_ver = pof_ver
        self.CHUNK_ID = chunk_id

    def read_chunk(self, bin_data):
        num_banks = unpack_int(bin_data.read(4))
        gun_points = list()
        gun_norms = list()

        for i in range(num_banks):
            num_guns = unpack_int(bin_data.read(4))
            gun_points.append(list())
            gun_norms.append(list())
            for j in range(num_guns):
                gun_points[i].append(unpack_vector(bin_data.read(12)))
                gun_norms[i].append(unpack_vector(bin_data.read(12)))

        self.gun_points = gun_points
        self.gun_norms = gun_norms

    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        logging.debug("Writing gun chunk with size {}...".format(length))

        gun_points = self.gun_points
        gun_norms = self.gun_norms

        num_banks = len(gun_points)
        chunk += pack_int(num_banks)

        for i in range(num_banks):
            num_guns = len(gun_points[i])
            chunk += pack_int(num_guns)
            for j in range(num_guns):
                chunk += pack_float(gun_points[i][j])
                chunk += pack_float(gun_norms[i][j])

        return chunk

    def __len__(self):
        try:
            chunk_length = 4
            gun_points = self.gun_points
            num_banks = len(gun_points)
            for i in range(num_banks):
                num_guns = len(gun_points[i])
                chunk_length += 4 + 24 * num_guns
            return chunk_length
        except AttributeError:
            return 0


class TurretChunk(POFChunk):           # TGUN and TMIS
    def __init__(self, pof_ver=2117, chunk_id=b'TGUN'):
        self.pof_ver = pof_ver
        self.CHUNK_ID = chunk_id

    def read_chunk(self, bin_data):
        num_banks = unpack_int(bin_data.read(4))

        barrel_sobj = list()
        base_sobj = list()
        turret_norm = list()
        firing_points = list()

        for i in range(num_banks):
            barrel_sobj.append(unpack_int(bin_data.read(4)))
            base_sobj.append(unpack_int(bin_data.read(4)))
            turret_norm.append(unpack_vector(bin_data.read(12)))
            num_firing_points = unpack_int(bin_data.read(4))

            firing_points.append(list())

            for j in range(num_firing_points):
                firing_points[i].append(unpack_vector(bin_data.read(12)))

        self.barrel_sobj = barrel_sobj
        self.base_sobj = base_sobj
        self.turret_norm = turret_norm
        self.firing_points = firing_points

    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        logging.debug("Writing turret chunk with size {}...".format(length))

        barrel_sobj = self.barrel_sobj
        base_sobj = self.base_sobj
        turret_norm = self.turret_norm
        firing_points = self.firing_points

        num_banks = len(firing_points)
        chunk += pack_int(num_banks)

        for i in range(num_banks):
            chunk += pack_int(barrel_sobj[i])
            chunk += pack_int(base_sobj[i])
            chunk += pack_float(turret_norm[i])

            num_firing_points = len(firing_points[i])
            chunk += pack_int(num_firing_points)

            for p in firing_points[i]:
                chunk += pack_float(p)

        return chunk

    def __len__(self):
        try:
            firing_points = self.firing_points
            chunk_length = 4 + 24 * len(firing_points)
            for i in firing_points:
                chunk_length += 12 * len(i)
            return chunk_length
        except AttributeError:
            return 0


class DockChunk(POFChunk):
    CHUNK_ID = b"DOCK"
    def read_chunk(self, bin_data):
        num_docks = unpack_int(bin_data.read(4))

        dock_properties = list()
        path_id = list()
        points = list()
        point_norms = list()

        for i in range(num_docks):
            str_len = unpack_int(bin_data.read(4))
            dock_properties.append(bin_data.read(str_len))
            num_paths = unpack_int(bin_data.read(4))

            path_id.append(list())

            for j in range(num_paths):
                path_id[i].append(unpack_int(bin_data.read(4)))

            num_points = unpack_int(bin_data.read(4))

            points.append(list())
            point_norms.append(list())

            for j in range(num_points):
                points[i].append(unpack_vector(bin_data.read(12)))
                point_norms[i].append(unpack_vector(bin_data.read(12)))

        self.dock_properties = dock_properties
        self.path_id = path_id
        self.points = points
        self.point_norms = point_norms

    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        logging.debug("Writing dock chunk with size {}...".format(length))

        dock_properties = self.dock_properties
        path_id = self.path_id
        points = self.points
        point_norms = self.point_norms

        num_docks = len(points)
        chunk += pack_int(num_docks)

        for i in range(num_docks):
            chunk += pack_string(dock_properties[i])
            num_paths = len(path_id[i])
            chunk += pack_int(num_paths)
            for j in range(num_paths):
                chunk += pack_int(path_id[i][j])
            num_points = len(points[i])
            chunk += pack_int(num_points)
            for j in range(num_points):
                chunk += pack_float(points[i][j])
                chunk += pack_float(point_norms[i][j])

        return chunk

    def __len__(self):
        try:
            chunk_length = 4
            dock_properties = self.dock_properties
            path_id = self.path_id
            points = self.points
            for i, s in enumerate(dock_properties):
                chunk_length += 4 + len(s)
                chunk_length += 4 * (len(path_id[i]) + 1)
                chunk_length += 24 * len(points[i]) + 4
            return chunk_length
        except AttributeError:
            return 0


class FuelChunk(POFChunk):
    CHUNK_ID = b"FUEL"
    def read_chunk(self, bin_data):
        pof_ver = self.pof_ver
        num_thrusters = unpack_int(bin_data.read(4))

        num_glows = list()
        if pof_ver >= 2117:
            thruster_properties = list()
        else:
            thruster_properties = None
        glow_pos = list()
        glow_norm = list()
        glow_radius = list()

        for i in range(num_thrusters):
            num_glows = unpack_int(bin_data.read(4))
            if pof_ver >= 2117:
                str_len = unpack_int(bin_data.read(4))
                thruster_properties.append(bin_data.read(str_len))

            glow_pos.append(list())
            glow_norm.append(list())
            glow_radius.append(list())

            for j in range(num_glows):
                glow_pos[i].append(unpack_vector(bin_data.read(12)))
                glow_norm[i].append(unpack_vector(bin_data.read(12)))
                glow_radius[i].append(unpack_float(bin_data.read(4)))

        self.thruster_properties = thruster_properties
        self.glow_pos = glow_pos
        self.glow_norm = glow_norm
        self.glow_radius = glow_radius

    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        logging.debug("Writing thruster chunk with size {}...".format(length))

        pof_ver = self.pof_ver

        if pof_ver >= 2117:
            thruster_properties = self.thruster_properties
        glow_pos = self.glow_pos
        glow_norm = self.glow_norm
        glow_radius = self.glow_radius

        num_thrusters = len(glow_pos)
        chunk += pack_int(num_thrusters)

        for i in range(num_thrusters):
            num_glows = len(glow_pos[i])
            chunk += pack_int(num_glows)
            if pof_ver >= 2117:
                chunk += pack_string(thruster_properties[i])
            for j in range(num_glows):
                chunk += pack_float(glow_pos[i][j])
                chunk += pack_float(glow_norm[i][j])
                chunk += pack_float(glow_radius[i][j])

        return chunk

    def __len__(self):
        try:
            chunk_length = 4
            glow_pos = self.glow_pos
            num_thrusters = len(glow_pos)
            pof_ver = self.pof_ver
            if pof_ver >= 2117:
                thruster_properties = self.thruster_properties

            for i in range(num_thrusters):
                if pof_ver >= 2117:
                    chunk_length += 8 + len(thruster_properties[i])
                num_glows = len(glow_pos[i])
                chunk_length += 28 * num_glows

            return chunk_length
        except AttributeError:
            return 0


class ModelChunk(POFChunk):
    def __init__(self, pof_ver=2117, chunk_id=b'PSPO'):
        if pof_ver >= 2116:
            self.CHUNK_ID = b"OBJ2"
        else:
            self.CHUNK_ID = b"SOBJ"

        self.pof_ver = pof_ver

    def read_chunk(self, bin_data):
        pof_ver = self.pof_ver

        self.model_id = unpack_int(bin_data.read(4))

        if pof_ver >= 2116:
            self.radius = unpack_float(bin_data.read(4))
            self.parent_id = unpack_int(bin_data.read(4))
            self.offset = unpack_vector(bin_data.read(12))
        else:
            self.parent_id = unpack_int(bin_data.read(4))
            self.offset = unpack_vector(bin_data.read(12))
            self.radius = unpack_float(bin_data.read(4))

        self.center = unpack_vector(bin_data.read(12))
        self.min = unpack_vector(bin_data.read(12))
        self.max = unpack_vector(bin_data.read(12))

        str_len = unpack_int(bin_data.read(4))
        self.name = bin_data.read(str_len)
        logging.debug("Unpacking submodel {}, ID {}".format(self.name, self.model_id))
        str_len = unpack_int(bin_data.read(4))
        self.properties = bin_data.read(str_len)
        self.movement_type = unpack_int(bin_data.read(4))
        self.movement_axis = unpack_int(bin_data.read(4))

        bin_data.seek(4, 1)     # int reserved, must be 0
        bsp_size = unpack_int(bin_data.read(4))
        bsp_tree = list()       # we'll unpack the BSP data as a list of chunks

        bsp_addr = bin_data.tell()
        self.bsp_data = bin_data.read(bsp_size)     # keep a packed version for caching purposes
        bin_data.seek(bsp_addr)

        logging.debug("BSP data size {}".format(bsp_size))

        while True:
            block_addr = bin_data.tell()
            eof_test = bin_data.read(4)
            bin_data.seek(block_addr)
            if eof_test != b"":
                block_id = unpack_int(bin_data.read(4))
                block_size = unpack_int(bin_data.read(4))
                if block_id != 0:
                    this_block = chunk_dict[block_id]()
                    this_block_data = RawData(bin_data.read(block_size - 8))
                    this_block.read_chunk(this_block_data)
                else:
                    this_block = EndBlock()
                bsp_tree.append(this_block)
            else:       # EOF
                break

        self.bsp_tree = bsp_tree

    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        logging.debug("Writing model chunk with size {}...".format(length))

        pof_ver = self.pof_ver

        chunk += pack_int(self.model_id)

        if pof_ver >= 2116:
            chunk += pack_float(self.radius)
            chunk += pack_int(self.parent_id)
            chunk += pack_float(self.offset)
        else:
            chunk += pack_int(self.parent_id)
            chunk += pack_float(self.offset)
            chunk += pack_float(self.radius)

        chunk += pack_float(self.center)
        chunk += pack_float(self.min)
        chunk += pack_float(self.max)

        chunk += pack_string(self.name)
        chunk += pack_string(self.properties)
        chunk += pack_int(self.movement_type)
        chunk += pack_int(self.movement_axis)
        chunk += b'\0\0\0\0'

        bsp_data = b""
        bsp_tree = self.bsp_tree

        for block in bsp_tree:
            bsp_data += block.write_chunk()

        logging.debug("And BSP data size {}...".format(len(bsp_data)))
        chunk += pack_int(len(bsp_data))
        chunk += bsp_data

        return chunk

    def get_mesh(self):
        """Returns a mesh object."""
        bsp_tree = self.bsp_tree
        raw_faces = list()

        for node in bsp_tree:
            if node.CHUNK_ID == 1:
                # get vert list from defpoints
                # should only happen once per model
                vert_list = node.vert_list
                num_norms = node.norm_counts
                #vert_norms = node.vert_norms
            elif node.CHUNK_ID == 2 or node.CHUNK_ID == 3:
                raw_faces.append(node)

        m = Mesh()
        m.verts = vert_list
        m.num_norms = num_norms
        # until I figure something out for Mesh, we have
        # to make our own Face list and Edge list
        face_list = list()
        uv = list()
        #vert_norms = list()
        tex_ids = list()
        for node in raw_faces:
            face_list.append(node.vert_list)
            if node.CHUNK_ID == 2:
                uv.append([[0,0]] * len(node.vert_list))
                tex_ids.append(None)
            else:
                uv.append(list(zip(node.u, node.v)))
                tex_ids.append(node.texture_id)
        m.faces = face_list
        #m.vnorms = vert_norms
        m.uv = uv
        m.tex_ids = tex_ids

        # m.calculate_sharp_edges()

        return m

    def set_mesh(self, m):
        """Creates a BSP tree as a list of blocks.
        
        May take a few minutes, depending on size of the model, so get some coffee."""
        # Basically:
        # defpoints = DefpointsBlock()
        # defpoints.set_mesh(m)
        # self._defpoints = defpoints
        # polylist = self._make_polylist(m)
        # self._polylist = polylist
        # self._generate_tree_recursion()
        # self.bsp_tree = self._defpoints + self._polylist
        
        m.calc_fradii()
        
        defpoints = DefpointsBlock()
        defpoints.set_mesh(m)
        self._defpoints = defpoints

        # make initial polylist
        face_list = list()
        for i, f in enumerate(m.face_list):
            cur_node = TexpolyBlock()
            cur_node.normal = m.fnorms[i]
            cur_node.center = m.centers[i]
            cur_node.radius = m.fradii[i]
            cur_node.texture_id = m.tex_ids[i]
            cur_node.vert_list = f
            cur_node.norm_list = m.vnorms[i]
            cur_node.u = m.u[i]
            cur_node.v = m.v[i]

            face_list.append(cur_node)
        max_pnt, min_pnt = self._get_bounds(face_list)
        ctr_pnt = self._get_split_plane(face_list)
        self.max = max_pnt
        self.min = min_pnt
        self.center = ctr_pnt[0]
        self.bsp_tree = list()
        self._generate_tree_recursion(face_list)
        self.bsp_tree.insert(0, self._defpoints)
        self.bsp_tree.append(EndBlock())

    def _add_faces(self, face_list):
        bsp_tree = self.bsp_tree
        defpoints = self._defpoints.vert_list
        max_pnt, min_pnt = self._get_bounds(face_list)
        bbox = BoundboxBlock()
        bbox.max = max_pnt
        bbox.min = min_pnt
        bsp_tree.append(bbox)
        bsp_tree += face_list
        bsp_tree.append(EndBlock())

        self.bsp_tree = bsp_tree

    def _make_split(self, ctr_pnt, max_axis, face_list):
        front_list = list()
        back_list = list()
        for f in face_list:
            if f.center[max_axis] >= ctr_pnt[max_axis]:
                front_list.append(f)
            else:
                back_list.append(f)
        return front_list, back_list

    def _get_bounds(self, face_list):
        verts = self._defpoints.vert_list
        verts_x = list()
        verts_y = list()
        verts_z = list()
        for f in face_list:
            for v in f.vert_list:
                verts_x.append(verts[v][0])
                verts_y.append(verts[v][1])
                verts_z.append(verts[v][2])
        max_x = max(verts_x) + 0.1
        max_y = max(verts_y) + 0.1
        max_z = max(verts_z) + 0.1
        min_x = min(verts_x) - 0.1
        min_y = min(verts_y) - 0.1
        min_z = min(verts_z) - 0.1
        max_pnt = vector(max_x, max_y, max_z)
        min_pnt = vector(min_x, min_y, min_z)
        return max_pnt, min_pnt

    def _get_split_plane(self, max_pnt, min_pnt):
        dx = max_pnt[0] - min_pnt[0]
        dy = max_pnt[1] - min_pnt[1]
        dz = max_pnt[2] - min_pnt[2]
        cx = min_pnt[0] + dx / 2
        cy = min_pnt[1] + dy / 2
        cz = min_pnt[2] + dz / 2
        ctr_pnt = vector(cx, cy, cz)
        if max([dx, dy, dz]) is dx:
            max_axis = 0
            node_norm = vector(1, 0, 0)
        elif max([dx, dy, dz]) is dy:
            max_axis = 1
            node_norm = vector(0, 1, 0)
        elif max([dx, dy, dz]) is dz:
            max_axis = 2
            node_norm = vector(0, 0, 1)
        return list(ctr_pnt), max_axis, node_norm

    def _generate_tree_recursion(self, face_list):
        if not len(face_list):
            # nothing to do...
            return
        # if only one, make a face
        if len(face_list) == 1:
            self._add_faces(face_list)
            return None
        elif len(face_list) == 2:
            if face_list[0].center == face_list[1].center:
                # make a face
                self._add_faces(face_list)
                return
            # we cheat and make the split based on the polys
            ax = face_list[0].center[0]     # first face center
            ay = face_list[0].center[1]
            az = face_list[0].center[2]
            bx = face_list[1].center[0]     # second face center
            by = face_list[1].center[1]
            bz = face_list[1].center[2]
            max_x = max([ax, bx])           # max point
            max_y = max([ay, by])
            max_z = max([az, bz])
            max_pnt = vector(max_x, max_y, max_z)
            min_x = min([ax, bx])           # min point
            min_y = min([ay, by])
            min_z = min([az, bz])
            min_pnt = vector(min_x, min_y, min_z)
            ctr_pnt, max_axis, node_norm = self._get_split_plane(max_pnt, min_pnt)
            front_list, back_list = self._make_split(ctr_pnt, max_axis, face_list)
            max_pnt = False
            min_pnt = False
        else:
            # get initial center point
            max_pnt, min_pnt = self._get_bounds(face_list)
            ctr_pnt, max_axis, node_norm = self._get_split_plane(max_pnt, min_pnt)
            front_list, back_list = self._make_split(ctr_pnt, max_axis, face_list)
            fnum = len(front_list)
            bnum = len(back_list)
            num_tries = 0
            real_tries = 0
            ratio = 2.0
            while not fnum or not bnum:
                # one of them doesn't have polys
                # make a new split point based on the one that does
                num_tries += 1
                real_tries += 1     # does not get decremented
                if real_tries > 500:
                    # panic, just dump polys into unordered list
                    self._add_faces(face_list)
                    return
                on_back = False
                if bnum:
                    if not on_back:     # bnum was zero, but now fnum is zero
                        on_back = True
                        num_tries = 1
                        ratio *= 0.5    # we'll have to use a smaller amount
                    bmax, bmin = self._get_bounds(back_list)
                    ctr_pnt, max_axis, node_norm = self._get_split_plane(bmax, bmin)
                    ctr_pnt[max_axis] += (-0.01 * ratio) * num_tries
                    front_list, back_list = self._make_split(ctr_pnt, max_axis, back_list)
                else:
                    if on_back:
                        on_back = False
                        num_tries = 1
                        ratio *= 0.5
                    fmax, fmin = self._get_bounds(front_list)
                    ctr_pnt, max_axis, node_norm = self._get_split_plane(fmax, fmin)
                    ctr_pnt[max_axis] += (0.01 * ratio) * num_tries
                    front_list, back_list = self._make_split(ctr_pnt, max_axis, front_list)
                fnum = len(front_list)
                bnum = len(back_list)
            num_tries = 0
            while num_tries <= 15 and (
                fnum + bnum != len(face_list) or
                fnum - bnum > 0.05 * (fnum + bnum) + 1 or
                (not fnum or not bnum)
            ):
                num_tries += 1
                if fnum > bnum:
                    front = 1
                else:
                    front = -1
                delta = max_pnt[max_axis] - min_pnt[max_axis]
                # move ctr pnt towards longest list:
                ctr_pnt[max_axis] += front * (delta / (num_tries + 1) ** 2)
                front_list, back_list = self._make_split(ctr_pnt, max_axis, face_list)
                fnum = len(front_list)
                bnum = len(back_list)

            # something bad happened and an empty list slipped through
            if not fnum or not bnum:
                self._add_faces(face_list)
                return
        # get actual min, max, make sortnorm
        if not max_pnt or not min_pnt:
            # only called if 2 faces in list
            max_pnt, min_pnt = self._get_bounds(face_list)
        bsp_tree = self.bsp_tree
        cur_node = SortnormBlock()
        cur_node.max = max_pnt
        cur_node.min = min_pnt
        cur_node.plane_normal = node_norm
        cur_node.plane_point = ctr_pnt
        cur_idx = len(bsp_tree)
        bsp_tree.append(cur_node)
        for i in range(3):
            bsp_tree.append(EndBlock())
        # recurse into front list
        self.bsp_tree = bsp_tree
        self._generate_tree_recursion(front_list)
        # get back offset
        back_offset = 0
        bsp_tree = self.bsp_tree
        for node in bsp_tree[cur_idx:]:
            back_offset += len(node)
        self.bsp_tree[cur_idx].back_offset = back_offset
        # recurse into back list
        self._generate_tree_recursion(back_list)

    def __len__(self):
        chunk_length = 84
        try:
            chunk_length += len(self.name)
            chunk_length += len(self.properties)
            bsp_tree = self.bsp_tree
            for block in bsp_tree:
                if block.CHUNK_ID == 0:
                    chunk_length += 8
                else:
                    chunk_length += len(block)
            return chunk_length
        except AttributeError:
            return 0


class SquadChunk(POFChunk):
    CHUNK_ID = b"INSG"
    def read_chunk(self, bin_data):
        num_insig = unpack_int(bin_data.read(4))
        insig_detail_level = list()
        vert_list = list()
        insig_offset = list()
        face_list = list()
        u_list = list()
        v_list = list()

        for i in range(num_insig):
            insig_detail_level.append(unpack_int(bin_data.read(4)))
            num_faces = unpack_int(bin_data.read(4))
            num_verts = unpack_int(bin_data.read(4))
            vert_list.append(list())

            for j in range(num_verts):
                vert_list[i].append(unpack_vector(bin_data.read(12)))

            insig_offset.append(unpack_vector(bin_data.read(12)))
            face_list.append(list())
            u_list.append(list())
            v_list.append(list())

            for j in range(num_faces):
                face_list[i].append(list())
                u_list[i].append(list())
                v_list[i].append(list())

                for k in range(3):
                    face_list[i][j].append(unpack_int(bin_data.read(4)))
                    u_list[i][j].append(unpack_float(bin_data.read(4)))
                    v_list[i][j].append(unpack_float(bin_data.read(4)))

        self.insig_detail_level = insig_detail_level
        self.vert_list = vert_list
        self.insig_offset = insig_offset
        self.face_list = face_list
        self.u_list = u_list
        self.v_list = v_list

    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        logging.debug("Writing insignia chunk with size {}...".format(length))

        insig_detail_level = self.insig_detail_level
        vert_list = self.vert_list
        insig_offset = self.insig_offset
        face_list = self.face_list
        u_list = self.u_list
        v_list = self.v_list

        num_insig = len(vert_list)
        chunk += pack_int(num_insig)

        for i in range(num_insig):
            chunk += pack_int(insig_detail_level[i])
            num_faces = len(face_list[i])
            num_verts = len(vert_list[i])
            chunk += pack_int(num_faces)
            chunk += pack_int(num_verts)

            for v in vert_list[i]:
                chunk += pack_float(v)

            chunk += pack_float(insig_offset[i])

            for j, f in enumerate(face_list[i]):
                for k in range(3):
                    chunk += pack_int(f[k])
                    chunk += pack_float(u_list[i][j][k])
                    chunk += pack_float(v_list[i][j][k])

        return chunk

    def get_mesh(self, insig_id=None):
        # if insig_id is None:
            # get all insignia,
            # return a list of Mesh objects
        pass

    def set_mesh(self, m, insig_id=None, insig_detail_level=False):
        # if insig_id is None:
            # m is a list of Mesh objects
            # insig_detail_level must be a list of detail levels
            # set all insignia
        pass

    def __len__(self):
        chunk_length = 4
        try:
            vert_list = self.vert_list
            face_list = self.face_list
            chunk_length += 24 * len(vert_list)
            for i in vert_list:
                chunk_length += 12 * len(i)
            for i in face_list:
                chunk_length += 36 * len(i)
            return chunk_length
        except AttributeError:
            return 0


class CenterChunk(POFChunk):
    CHUNK_ID = b"ACEN"
    def read_chunk(self, bin_data):
        self.co = unpack_vector(bin_data.read(12))

    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        logging.debug("Writing center chunk with size {}...".format(length))

        chunk += pack_float(self.co)

        return chunk

    def __len__(self):
        try:
            if self.co:
                return 12
        except AttributeError:
            return 0


class GlowChunk(POFChunk):
    CHUNK_ID = b"GLOW"
    def read_chunk(self, bin_data):
        num_banks = unpack_int(bin_data.read(4))
        disp_time = list()
        on_time = list()
        off_time = list()
        parent_id = list()
        properties = list()

        glow_points = list()
        glow_norms = list()
        glow_radius = list()

        for i in range(num_banks):
            disp_time.append(unpack_int(bin_data.read(4)))
            on_time.append(unpack_int(bin_data.read(4)))
            off_time.append(unpack_int(bin_data.read(4)))
            parent_id.append(unpack_int(bin_data.read(4)))
            bin_data.seek(8, 1)
            num_glows = unpack_int(bin_data.read(4))
            str_len = unpack_int(bin_data.read(4))
            properties.append(bin_data.read(str_len))

            glow_points.append(list())
            glow_norms.append(list())
            glow_radius.append(list())

            for j in range(num_glows):
                glow_points[i].append(unpack_vector(bin_data.read(12)))
                glow_norms[i].append(unpack_vector(bin_data.read(12)))
                glow_radius[i].append(unpack_float(bin_data.read(4)))

        self.disp_time = disp_time
        self.on_time = on_time
        self.off_time = off_time
        self.parent_id = parent_id
        self.properties = properties
        self.glow_points = glow_points
        self.glow_norms = glow_norms
        self.glow_radius = glow_radius

    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        logging.debug("Writing glowpoint chunk with size {}...".format(length))

        disp_time = self.disp_time
        on_time = self.on_time
        off_time = self.off_time
        parent_id = self.parent_id
        properties = self.properties
        glow_points = self.glow_points
        glow_norms = self.glow_norms
        glow_radius = self.glow_radius

        num_banks = len(glow_points)
        chunk += pack_int(num_banks)

        for i in range(num_banks):
            num_glows = len(glow_points[i])
            chunk += pack_int([disp_time[i],
                               on_time[i],
                               off_time[i],
                               parent_id[i],
                               0,
                               0,
                               num_glows])
            chunk += pack_string(properties[i])
            for j in range(num_glows):
                chunk += pack_float(glow_points[i][j])
                chunk += pack_float(glow_norms[i][j])
                chunk += pack_float(glow_radius[i][j])

        return chunk

    def __len__(self):
        chunk_length = 4
        try:
            glow_points = self.glow_points
            properties = self.properties
            chunk_length += 28 * len(glow_points)
            for s in properties:
                chunk_length += 4 + len(s)
            for p in glow_points:
                chunk_length += 28 * len(p)
            return chunk_length
        except AttributeError:
            return 0


class TreeChunk(POFChunk):
    CHUNK_ID = b"SLDC"
    def read_chunk(self, bin_data):
        tree_size = unpack_uint(bin_data.read(4))
        shield_tree = list()

        while True:
            node_type = unpack_ubyte(bin_data.read(1))
            eof_test = bin_data.read(4)
            if eof_test == b"":
                break
            if not node_type:
                this_node = ShieldSplit()
                this_node.min = unpack_vector(bin_data.read(12))
                this_node.max = unpack_vector(bin_data.read(12))
                this_node.front = unpack_uint(bin_data.read(4))
                this_node.back = unpack_uint(bin_data.read(4))
            else:
                this_node = ShieldLeaf()
                this_node.min = unpack_vector(bin_data.read(12))
                this_node.max = unpack_vector(bin_data.read(12))
                num_polygons = unpack_uint(bin_data.read(4))
                face_list = list()
                for i in range(num_polygons):
                    face_list.append(unpack_uint(bin_data.read(4)))
                this_node.face_list = face_list
            shield_tree.append(this_node)
            self.shield_tree = shield_tree

    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False
        logging.debug("Writing shield collision tree with size {}...".format(length))
        chunk += pack_uint(length - 4)

        shield_tree = self.shield_tree

        for node in shield_tree:
            chunk += pack_ubyte(node.node_type)
            chunk += pack_uint(len(node))

            if node.node_type:
                chunk += pack_float(node.min)
                chunk += pack_float(node.max)

                face_list = node.face_list
                num_polygons = len(face_list)
                chunk += pack_uint(num_polygons)

                for f in face_list:
                    chunk += pack_uint(f)

        return chunk

    def make_shield_collision_tree(self, shield_chunk=None, m=None):
        """Should be called if any geometry on the shield is modified."""
        if m is not None:
            if shield_chunk is not None:
                shield_chunk.set_mesh(m)
        else:
            if shield_chunk is not None:
                m = shield_chunk.get_mesh()
            else:
                raise InvalidChunkError(self, "Must have either shield chunk or mesh")

        face_list = m.face_list     # Hopefully the same index as the shield chunk

        self.shield_tree = list()
        self._generate_tree_recursion(face_list)

    def _add_faces(self, face_list):
        cur_node = ShieldLeaf()
        max_pnt, min_pnt = self._get_bounds(face_list)
        cur_node.max = max_pnt
        cur_node.min = min_pnt
        for f in face_list:
            cur_node.face_list.append(f.face_idx)
        self.shield_tree.append(cur_node)

    def _make_split(self, ctr_pnt, max_axis, face_list):
        front_list = list()
        back_list = list()
        for f in face_list:
            if f.center[max_axis] >= ctr_pnt[max_axis]:
                front_list.append(f)
            else:
                back_list.append(f)
        return front_list, back_list

    def _get_bounds(self, face_list):
        verts_x = list()
        verts_y = list()
        verts_z = list()
        for f in face_list:
            for v in f.vert_list:
                verts_x.append(v.co[0])
                verts_y.append(v.co[1])
                verts_z.append(v.co[2])
        max_x = max(verts_x) + 0.1
        max_y = max(verts_y) + 0.1
        max_z = max(verts_z) + 0.1
        min_x = min(verts_x) - 0.1
        min_y = min(verts_y) - 0.1
        min_z = min(verts_z) - 0.1
        max_pnt = vector(max_x, max_y, max_z)
        min_pnt = vector(min_x, min_y, min_z)
        return max_pnt, min_pnt

    def _get_split_plane(self, max_pnt, min_pnt):
        dx = max_pnt[0] - min_pnt[0]
        dy = max_pnt[1] - min_pnt[1]
        dz = max_pnt[2] - min_pnt[2]
        cx = min_pnt[0] + dx / 2
        cy = min_pnt[1] + dy / 2
        cz = min_pnt[2] + dz / 2
        ctr_pnt = vector(cx, cy, cz)
        if max([dx, dy, dz]) is dx:
            max_axis = 0
            node_norm = vector(1, 0, 0)
        elif max([dx, dy, dz]) is dy:
            max_axis = 1
            node_norm = vector(0, 1, 0)
        elif max([dx, dy, dz]) is dz:
            max_axis = 2
            node_norm = vector(0, 0, 1)
        return list(ctr_pnt), max_axis, node_norm

    def _generate_tree_recursion(self, face_list):
        if not len(face_list):
            # nothing to do...
            return
        # if only one, make a face
        if len(face_list) == 1:
            self._add_faces(face_list)
            return None
        elif len(face_list) == 2:
            if face_list[0].center == face_list[1].center:
                # make a face
                self._add_faces(face_list)
                return
            # we cheat and make the split based on the polys
            ax = face_list[0].center[0]     # first face center
            ay = face_list[0].center[1]
            az = face_list[0].center[2]
            bx = face_list[1].center[0]     # second face center
            by = face_list[1].center[1]
            bz = face_list[1].center[2]
            max_x = max([ax, bx])           # max point
            max_y = max([ay, by])
            max_z = max([az, bz])
            max_pnt = vector(max_x, max_y, max_z)
            min_x = min([ax, bx])           # min point
            min_y = min([ay, by])
            min_z = min([az, bz])
            min_pnt = vector(min_x, min_y, min_z)
            ctr_pnt, max_axis, node_norm = self._get_split_plane(max_pnt, min_pnt)
            front_list, back_list = self._make_split(ctr_pnt, max_axis, face_list)
            max_pnt = False
            min_pnt = False
        else:
            # get initial center point
            max_pnt, min_pnt = self._get_bounds(face_list)
            ctr_pnt, max_axis, node_norm = self._get_split_plane(max_pnt, min_pnt)
            front_list, back_list = self._make_split(ctr_pnt, max_axis, face_list)
            fnum = len(front_list)
            bnum = len(back_list)
            num_tries = 0
            real_tries = 0
            ratio = 2.0
            while not fnum or not bnum:
                # one of them doesn't have polys
                # make a new split point based on the one that does
                num_tries += 1
                real_tries += 1     # does not get decremented
                if real_tries > 500:
                    # panic, just dump polys into unordered list
                    self._add_faces(face_list)
                    return
                on_back = False
                if bnum:
                    if not on_back:     # bnum was zero, but now fnum is zero
                        on_back = True
                        num_tries = 1
                        ratio *= 0.5    # we'll have to use a smaller amount
                    bmax, bmin = self._get_bounds(back_list)
                    ctr_pnt, max_axis, node_norm = self._get_split_plane(bmax, bmin)
                    ctr_pnt[max_axis] += (-0.01 * ratio) * num_tries
                    front_list, back_list = self._make_split(ctr_pnt, max_axis, back_list)
                else:
                    if on_back:
                        on_back = False
                        num_tries = 1
                        ratio *= 0.5
                    fmax, fmin = self._get_bounds(front_list)
                    ctr_pnt, max_axis, node_norm = self._get_split_plane(fmax, fmin)
                    ctr_pnt[max_axis] += (0.01 * ratio) * num_tries
                    front_list, back_list = self._make_split(ctr_pnt, max_axis, front_list)
                fnum = len(front_list)
                bnum = len(back_list)
            num_tries = 0
            while num_tries <= 15 and (
                fnum + bnum != len(face_list) or
                fnum - bnum > 0.05 * (fnum + bnum) + 1 or
                (not fnum or not bnum)
            ):
                num_tries += 1
                if fnum > bnum:
                    front = 1
                else:
                    front = -1
                delta = max_pnt[max_axis] - min_pnt[max_axis]
                # move ctr pnt towards longest list:
                ctr_pnt[max_axis] += front * (delta / (num_tries + 1) ** 2)
                front_list, back_list = self._make_split(ctr_pnt, max_axis, face_list)
                fnum = len(front_list)
                bnum = len(back_list)

            # something bad happened and an empty list slipped through
            if not fnum or not bnum:
                self._add_faces(face_list)
                return
        # get actual min, max, make sortnorm
        if not max_pnt or not min_pnt:
            # only called if 2 faces in list
            max_pnt, min_pnt = self._get_bounds(face_list)
        shield_tree = self.shield_tree
        cur_node = ShieldSplit()
        cur_node.max = max_pnt
        cur_node.min = min_pnt
        cur_idx = len(shield_tree)
        shield_tree.append(cur_node)
        # recurse into front list
        self.shield_tree = shield_tree
        self._generate_tree_recursion(front_list)
        # get back offset
        back_offset = 0
        shield_tree = self.shield_tree
        for node in shield_tree[cur_idx:]:
            back_offset += len(node)
        self.shield_tree[cur_idx].back_offset = back_offset
        # recurse into back list
        self._generate_tree_recursion(back_list)

    def __len__(self):
        chunk_length = 4
        try:
            shield_tree = self.shield_tree
            for node in shield_tree:
                chunk_length += len(node)
            return chunk_length
        except AttributeError:
            return 0


class ShieldSplit:
    node_type = 0
    min = None
    max = None
    front_offset = 37
    back_offset = None

    def __len__(self):
        return 37


class ShieldLeaf:
    node_type = 1
    min = None
    max = None
    face_list = list()

    def __len__(self):
        return 33 + 4 * len(self.face_list)


class EndBlock(POFChunk):
    CHUNK_ID = 0
    def read_chunk(self, bin_data):
        pass

    def write_chunk(self):
        return b"\0\0\0\0\0\0\0\0"

    def __len__(self):
        return 8


class DefpointsBlock(POFChunk):
    CHUNK_ID = 1
    def read_chunk(self, bin_data):
        num_verts = unpack_int(bin_data.read(4))
        num_norms = unpack_int(bin_data.read(4))
        vert_data_offset = unpack_int(bin_data.read(4))

        norm_counts = list()

        for i in range(num_verts):
            norm_counts.append(unpack_byte(bin_data.read(1)))

        self.norm_counts = norm_counts

        if bin_data.tell() != vert_data_offset - 8:
            logging.warning("DEFPOINTS:Current location does not equal vert data offset")
            bin_data.seek(vert_data_offset - 8)

        vert_list = list()
        vert_norms = list()

        for i in range(num_verts):
            vert_list.append(unpack_vector(bin_data.read(12)))
            vert_norms.append(list())
            for j in range(norm_counts[i]):
                vert_norms[i].append(unpack_vector(bin_data.read(12)))

        self.vert_list = vert_list
        self.vert_norms = vert_norms

    def write_chunk(self):
        chunk = pack_int(self.CHUNK_ID)
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        vert_list = self.vert_list
        vert_norms = self.vert_norms
        num_verts = len(vert_list)
        num_norms = 0
        vert_data_offset = 20 + num_verts

        for v in vert_norms:
            num_norms += len(v)

        chunk += pack_int(num_verts)
        chunk += pack_int(num_norms)
        chunk += pack_int(vert_data_offset)

        for v in vert_norms:
            chunk += pack_byte(len(v))      # norm counts

        for i, v in enumerate(vert_norms):
            chunk += pack_float(vert_list[i])
            for n in v:
                chunk += pack_float(n)

        return chunk

    def get_mesh(self, m=False):
        if not m:
            m = Mesh()
        m.verts = self.vert_list
        m.num_norms = self.norm_counts

        return m

    def set_mesh(self, m):
        self.vert_list = m.verts
        self.vert_norms = m.vnorms

    def __len__(self):
        chunk_length = 20
        try:
            vert_norms = self.vert_norms
            for v in vert_norms:
                chunk_length += 13 + 12 * len(v)
            return chunk_length
        except AttributeError:
            return 0


class FlatpolyBlock(POFChunk):
    CHUNK_ID = 2
    def read_chunk(self, bin_data):
        self.normal = unpack_vector(bin_data.read(12))
        self.center = unpack_vector(bin_data.read(12))
        self.radius = unpack_float(bin_data.read(4))
        num_verts = unpack_int(bin_data.read(4))            # should always be 3
        self.color = unpack_ubyte(bin_data.read(4))         # (r, g, b, pad_byte)

        vert_list = list()
        norm_list = list()

        for i in range(num_verts):
            vert_list.append(unpack_short(bin_data.read(2)))
            norm_list.append(unpack_short(bin_data.read(2)))

        self.vert_list = vert_list      # indexed into DefpointsBlock.vert_list
        self.norm_list = norm_list      # indexed into DefpointsBlock.vert_norms[i]

    def write_chunk(self):
        chunk = pack_int(self.CHUNK_ID)
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        vert_list = self.vert_list
        norm_list = self.norm_list

        chunk += pack_float(self.normal)
        chunk += pack_float(self.center)
        chunk += pack_float(self.radius)
        chunk += pack_int(len(self.vert_list))
        chunk += pack_ubyte(self.color)

        for n, v in zip(norm_list, vert_list):
            chunk += pack_short(v)
            chunk += pack_short(n)

        return chunk

    def __len__(self):
        chunk_length = 44
        try:
            chunk_length += 4 * len(vert_list)
            return chunk_length
        except AttributeError:
            return 0


class TexpolyBlock(POFChunk):
    CHUNK_ID = 3
    def read_chunk(self, bin_data):
        self.normal = unpack_vector(bin_data.read(12))
        self.center = unpack_vector(bin_data.read(12))
        self.radius = unpack_float(bin_data.read(4))
        num_verts = unpack_int(bin_data.read(4))
        self.texture_id = unpack_int(bin_data.read(4))

        vert_list = list()
        norm_list = list()
        u = list()
        v = list()

        for i in range(num_verts):
            vert_list.append(unpack_ushort(bin_data.read(2)))
            norm_list.append(unpack_ushort(bin_data.read(2)))
            u.append(unpack_float(bin_data.read(4)))
            v.append(unpack_float(bin_data.read(4)))

        self.vert_list = vert_list
        self.norm_list = norm_list
        self.u = u
        self.v = v

    def write_chunk(self):
        chunk = pack_int(self.CHUNK_ID)
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False

        vert_list = self.vert_list
        norm_list = self.norm_list
        u = self.u
        v = self.v

        chunk += pack_float(self.normal)
        chunk += pack_float(self.center)
        chunk += pack_float(self.radius)
        chunk += pack_int(len(vert_list))
        chunk += pack_int(self.texture_id)

        for i, vert in enumerate(vert_list):
            chunk += pack_ushort(vert)
            chunk += pack_ushort(norm_list[i])
            chunk += pack_float(u[i])
            chunk += pack_float(v[i])

        return chunk

    def __len__(self):
        chunk_length = 44
        try:
            chunk_length += 12 * len(self.vert_list)
            return chunk_length
        except AttributeError:
            return 0


class SortnormBlock(POFChunk):
    CHUNK_ID = 4
    front_offset = 104
    prelist_offset = 80
    postlist_offset = 88
    online_offset = 96
    def read_chunk(self, bin_data):
        self.plane_normal = unpack_vector(bin_data.read(12))
        self.plane_point = unpack_vector(bin_data.read(12))
        bin_data.seek(4, 1)     # int reserved = 0
        self.front_offset = unpack_int(bin_data.read(4))
        self.back_offset = unpack_int(bin_data.read(4))
        self.prelist_offset = unpack_int(bin_data.read(4))
        self.postlist_offset = unpack_int(bin_data.read(4))
        self.online_offset = unpack_int(bin_data.read(4))
        self.min = unpack_vector(bin_data.read(12))
        self.max = unpack_vector(bin_data.read(12))

    def write_chunk(self):
        chunk = pack_int(self.CHUNK_ID)
        chunk += pack_int(80)

        chunk += pack_float(self.plane_normal)
        chunk += pack_float(self.plane_point)
        chunk += b'\0\0\0\0'
        chunk += pack_int(self.front_offset)
        chunk += pack_int(self.back_offset)
        chunk += pack_int(self.prelist_offset)
        chunk += pack_int(self.postlist_offset)
        chunk += pack_int(self.online_offset)
        chunk += pack_float(self.min)
        chunk += pack_float(self.max)

        return chunk

    def __len__(self):
        return 80


class BoundboxBlock(POFChunk):
    CHUNK_ID = 5
    def read_chunk(self, bin_data):
        self.min = unpack_vector(bin_data.read(12))
        self.max = unpack_vector(bin_data.read(12))

    def write_chunk(self):
        chunk = [pack_int(self.CHUNK_ID),
                      pack_int(32),
                      pack_float(self.min),
                      pack_float(self.min)]
        return b"".join(chunk)

    def __len__(self):
        return 32


chunk_dict = { # chunk or block id : chunk class
              b"HDR2": HeaderChunk,
              b"OHDR": HeaderChunk,
              b"TXTR": TextureChunk,
              b"PINF": MiscChunk,
              b"PATH": PathChunk,
              b"SPCL": SpecialChunk,
              b"SHLD": ShieldChunk,
              b" EYE": EyeChunk,
              b"EYE ": EyeChunk,
              b"GPNT": GunChunk,
              b"MPNT": GunChunk,
              b"TGUN": TurretChunk,
              b"TMIS": TurretChunk,
              b"DOCK": DockChunk,
              b"FUEL": FuelChunk,
              b"SOBJ": ModelChunk,
              b"OBJ2": ModelChunk,
              b"INSG": SquadChunk,
              b"ACEN": CenterChunk,
              b"GLOW": GlowChunk,
              b"SLDC": TreeChunk,
              0: EndBlock,
              1: DefpointsBlock,
              2: FlatpolyBlock,
              3: TexpolyBlock,
              4: SortnormBlock,
              5: BoundboxBlock}


chunk_order = {
               "TXTR": 0,
               "HDR2": 1,
               "OHDR": 1,
               "SPCL": 2,
               "GPNT": 3,
               "MPNT": 4,
               "TGUN": 5,
               "TMIS": 6,
               "DOCK": 7,
               "FUEL": 8,
               "SHLD": 9,
               " EYE": 10,
               "EYE ": 10,
               "ACEN": 11,
               "PATH": 12,
               "GLOW": 13,
               "SLDC": 14,
               "PINF": 15}


## Module methods ##


def read_pof(pof_file):
    """Takes a file-like object as a required argument, returns a list of chunks."""

    logging.info("Reading POF file from {}".format(pof_file))

    file_id = pof_file.read(4)
    if file_id != b'PSPO':
        raise FileFormatError(file_id, "Incorrect file ID for POF file")

    file_version = unpack_int(pof_file.read(4))
    logging.debug("POF file version {}".format(file_version))
    if file_version > 2117:
        raise FileFormatError(file_version, "Expected POF version 2117 or lower, file version")

    chunk_list = list()

    while True:
        chunk_id = pof_file.read(4)
        logging.debug("Found chunk {}".format(chunk_id))
        if chunk_id != b"":
            chunk_length = unpack_int(pof_file.read(4))
            logging.debug("Chunk length {}".format(chunk_length))
            try:
                this_chunk = chunk_dict[chunk_id](file_version, chunk_id)
            except KeyError:        # skip over unknown chunk
                logging.warning("Unknown chunk {}, skipping...".format(chunk_id))
                pof_file.seek(chunk_length, 1)
                continue
            chunk_data = RawData(pof_file.read(chunk_length))
            this_chunk.read_chunk(chunk_data)
            chunk_list.append(this_chunk)
        else:       # EOF
            logging.info("End of file.")
            break

    poly_model = PolyModel(chunk_list, file_version)

    return poly_model


def write_pof(polymodel, pof_version=2117):
    polymodel.verify_pof(pof_version)
    chunk_list = polymodel.get_chunk_list()

    pof_file = b"".join([b'PSPO', pack_int(pof_version)])

    for chunk in chunk_list:
        print("Writing chunk {}".format(chunk.CHUNK_ID))
        pof_file += chunk.write_chunk()

    return pof_file

