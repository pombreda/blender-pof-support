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

## TO DO LIST:

## Helpers
# Mesh
## Chunks
# ShieldChunk
    # get_mesh() - creates and returns a Mesh object
    # set_mesh(mesh) - parses a Mesh object to fill out the chunk attributes
# EyeChunk
# GunChunk
# TurretChunk
# DockChunk
# ThrusterChunk
# SubmodelChunk
    # get_mesh()
    # set_mesh(mesh)
    # make_bsp_tree()
# LogoChunk
# CenterChunk
# GlowpointChunk
# ShieldCollisionChunk
# DefpointsBlock
# EndBlock
# FlatpolyBlock
# TmappolyBlock
# SortnormBlock
# BoundboxBlock
## POF and BSP functions
# read_pof()
# write_pof()
# make_defpoints()
# make_polylist()
# generate_tree_recursion()

from math import fsum, sqrt
from bintools import *
from . import VolitionError, FileFormatError

## Exceptions ##
        
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
        
class VertListError(GeometryError):
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
            
def vector(x = False, y = False, z = False):
    """A sequence of floats.  Returns a tuple.

    Attributes:
        x=0 -- float -- x-axis point
        y=0 -- float -- y-axis point
        z=0 -- float -- z-axis point"""
    if not x or not y or not z:
        return False
    else:
        return (float(x), float(y), float(z))
        
class Mesh:
    """A Mesh object.
    
    Attributes:
        vert_list - a sequence of Vertex Objects
        edge_list - a sequence of Edge Objects
        face_list - a sequence of Face Objects
        
    Methods:
        get_vert_list() - parses self.vert_list and returns a list of vertex coordinates
        set_vert_list(vert_list, vert_norms = False) - parses a list of vertex coordinates and, optionally, a list of vertex normals to self.vert_list
        get_edge_list() - parses self.edge_list and returns a list in the format [[u0, v0, s0], [u1, v1, s1], ...], where ui and vi are indexed into self.vert_list and si is the boolean seam value
        set_edge_list(edge_list) - parses a list in the same format as returned by get_edge_list() to self.edge_list
        get_face_list(by_edges = False) - parses self.face_list and returns a list in the format [[vert_idx], [face_norms]] or, if by_edges is True, [[edge_idx], [face_norms]]
        set_face_list(face_list, vert_norms = False, by_edges = False) - parses a list of faces where each face is either a vert index or an edge index
        calculate_normals() - calculates vertex normals for all the objects in vert_list, edge_list, and face_list
        get_vert_normals(format = "vertex") - returns a list of vertex normals indexed to the mesh's vert list or, optionally, the edge list's or face list's vertex lists
    """
    def __init__(self, vert_list=False, edge_list=False, face_list=False):
        self.vert_list = vert_list
        self.edge_list = edge_list
        self.face_list = face_list
        
        try:
            self._make_index()
        except (AttributeError, IndexError, KeyError, NameError, TypeError, ValueError):
            self._fei = False
            self._fvi = False
            self._evi = False
            self._efi = False
            self._vfi = False
            self._vei = False
        
    def get_vert_list(self):
        """Returns a list of vertex coordinates."""
    
        vert_list = list()
        verts = self.vert_list
        for v in verts:
            vert_list.append(v.co)
            
        return vert_list
        
    def set_vert_list(self, vert_list, vert_norms = False):
        """Takes a list of vertex coordinates and creates a set of Vertex objects."""
                
        verts = set()
        if vert_norms:
            for v, n in zip(vert_list, vert_norms):
                verts.add(Vertex(v, n))
        else:
            for v in vert_list:
                verts.add(Vertex(v))
        self.vert_list = verts
                
        try:
            self._make_index()
        except (AttributeError, IndexError, KeyError, NameError, TypeError, ValueError):
            self._fei = False
            self._fvi = False
            self._evi = False
            self._efi = False
            self._vfi = False
            self._vei = False
        
    def get_edge_list(self):
            
        if not self._evi:
            try:
                self._make_index()
            except (AttributeError, IndexError, KeyError, NameError, TypeError, ValueError):
                raise GeometryError(None, "Incomplete geometry - can't make index.")
                
        edge_list = self._evi.values()
        
        edges = self.edge_list
        for i, e in enumerate(edges):
            edge_list[i].append(e.seam)
            
        return edge_list
        
    def set_edge_list(self, edge_list):
            
        edges = set()
        for e in edge_list:
            edges.add(Edge(e[:2], e[2]))
            
        try:
            self._make_index()
        except (AttributeError, IndexError, KeyError, NameError, TypeError, ValueError):
            self._fei = False
            self._fvi = False
            self._evi = False
            self._efi = False
            self._vfi = False
            self._vei = False
        
    def get_face_list(self, by_edges = False):
            
        if not self._fei or not self._fvi:
            try:
                self._make_index()
            except (AttributeError, IndexError, KeyError, NameError, TypeError, ValueError):
                raise GeometryError(None, "Incomplete geometry - can't make index.")
                
        if by_edges:
            face_list = [self._fei.values(), []]
        else:
            face_list = [self._fvi.values(), []]
            
        faces = self.face_list
        for f in faces:
            face_list[1].append(f.normal)
            
        return face_list
        
    def set_face_list(self, face_list, by_edges = False):
                
        faces = set()
        
        # We want to support both by_edges and !by_edges
        # because the face list will be by edges when
        # exporting, but by verts when importing.
        
        if by_edges:
            edges = list(self.edge_list)
            for f in face_list:
                edge_a = edges[f[0]]
                edge_b = edges[f[1]]
                edge_c = edges[f[2]]
                faces.add(Face([edge_a, edge_b, edge_c]))
        else:
            verts = list(self.vert_list)
            edges = self.edge_list
            for f in face_list:
                edge_a_verts = (verts[f[0]], verts[f[1]])
                edge_b_verts = (verts[f[1]], verts[f[2]])
                edge_c_verts = (verts[f[2]], verts[f[0]])
                
                edge_a = Edge(edge_a_verts)
                edge_b = Edge(edge_b_verts)
                edge_c = Edge(edge_c_verts)
                
                edges.add(edge_a)
                edges.add(edge_b)
                edges.add(edge_c)
                
                faces.add(Face([edge_a, edge_b, edge_c]))
                self.edge_list = edges
                
        self.face_list = faces
                
        try:
            self._make_index()
        except (AttributeError, IndexError, KeyError, NameError, TypeError, ValueError):
            self._fei = False
            self._fvi = False
            self._evi = False
            self._efi = False
            self._vfi = False
            self._vei = False
        
    def calculate_normals(self):
    
        # This should be called during export, where we have seam values
        # This should not be called during import, where we already have vertex normals
    
        fei = self._fei        # face edge index
        fvi = self._fvi        # face vert index
        
        evi = self._evi        # edge vert index
        efi = self._efi        # edge face index
        
        vfi = self._vfi        # vert face index
        vei = self._vei        # vert edge index
        
        if not fei or not fvi or not evi or not efi or not vfi or not vei:
            try:
                self._make_index()
            except (AttributeError, IndexError, KeyError, NameError, TypeError, ValueError):
                raise GeometryError(None, "Incomplete geometry - can't make index.")
        
        faces = self.face_list
        edges = self.edge_list
        verts = self.vert_list
                    
        for v, el in vei:
            smooth_norm_x = 0
            smooth_norm_y = 0
            smooth_norm_z = 0
            
            num_smooth_norms = 0
            
            this_vert_norms = set()     # using a set to avoid duplicates - will convert to list() later
            
            for e in el:
                if edges[e].seam:
                    for f in efi[e]:
                        smooth_norm_x += faces[f].normal[0]
                        smooth_norm_y += faces[f].normal[1]
                        smooth_norm_z += faces[f].normal[2]
                        num_smooth_norms += 1
                else:
                    for f in efi[e]:
                        this_vert_norms.add(faces[f].normal)
                        
            if num_smooth_norms:    # average face normals to get vertex normal
                smooth_norm_x /= num_smooth_norms
                smooth_norm_y /= num_smooth_norms
                smooth_norm_z /= num_smooth_norms
                this_vert_norms.add(vector(smooth_norm_x, smooth_norm_y, smooth_norm_z))
                
            verts[v].normals = list(this_vert_norms)
            
        # assign vert norm index to faces
                
        for v, fl in vfi:
            for f in fl:
                cur_vert_idx = fvi[f].index(v)
                for e in fei[f]:
                    if edges[e].seam:
                        faces[f].vert_norms[cur_vert_idx] = verts[v].normals.index(faces[f].normal)
                    else:
                        faces[f].vert_norms[cur_vert_idx] = len(verts[v].normals) - 1
            
        self.vert_list = verts
        self.face_list = faces
        self.edge_list = edges
        
    def _make_index(self):
        fei = dict()        # face edge index
        fvi = dict()        # face vert index
        
        evi = dict()        # edge vert index
        efi = dict()        # edge face index
        
        vfi = dict()        # vert face index
        vei = dict()        # vert edge index
        
        faces = self.face_list
        edges = self.edge_list
        verts = self.vert_list
        
        for i, f in enumerate(faces):        
            fe = set()     # list of indices
            fv = set()      # set of indices
            for e in f.edges:
                fe.add(edges.index(e))
                fv.add(verts.index(e.verts[0]), verts.index(e.verts[1]))
            fei[i] = fe
            fvi[i] = fv
            
        for i, e in enumerate(edges):
            evi[i] = set(verts.index(e.verts[0]), verts.index(e.verts[1])
            ef = set()
            for j, k in fei:
                if i in k:
                    ef.add(j)
            efi[i] = ef
            
        for i in len(verts):
            ve = set()
            vf = set()
            for j, k in evi:
                if i in k:
                    ve.add(j)
            for j, k in fvi:
                if i in k:
                    ve.add(j)
            vei[i] = ve
            vfi[i] = vf
            
        self._fei = fei
        self._fvi = fvi
        self._evi = evi
        self._efi = efi
        self._vfi = vfi
        self._vei = vei
        
class Vertex:
    """A Vertex object.
    
    Attributes:
        co (vector) -- The 3D coordinates of the vertex
        norms (sequence of vectors) -- The normals of the vertex"""
    def __init__(self, loc, norms = False):
        self.co = vector(loc)
        if norms:
            self.normals = list(norms)
            
    def __eq__(self, other):
        if self.co == other.co:
            return True
        else:
            return False
            
    def __hash__(self):
        return self.co
        
    def __repr__(self):
        return "<volition.Vertex object with coords {}>".format(self.co)
        
    def __str__(self):
        return str(self.co)
            
class Edge:
    def __init__(self, verts, seam = True):
        if not isinstance(verts[0], Vertex) or not isinstance(verts[1], Vertex) or len(verts) != 2:
            raise VertListError(verts, "Vertex list for Edge object instantiation must be sequence of two Vertex objects.")
        else:
            self.verts = verts
            self.seam = seam
            self.length = sqrt((verts[1].co[0] - verts[0].co[0]) ** 2 + (verts[1].co[1] - verts[0].co[1]) ** 2 + (verts[1].co[2] - verts[0].co[2]) ** 2)
            
    def __eq__(self, other):
        if self.verts == other.verts:
            return True
        else:
            return False
            
    def __hash__(self):
        return self.verts
        
    def __repr__(self):
        return "<volition.Edge object with vertices {}>".format(str(self.verts))
        
    def __str__(self):
        return str(self.verts)
            
class Face:
    def __init__(self, edge_list):
        try:
            prev_edge_verts = edge_list[len(edge_list) - 1].verts
        except (AttributeError, ValueError, IndexError, TypeError):
            raise FaceListError(edge_list, "Face must be instantiated from a sequence of Edge objects.")
            
        for e in edge_list:
            if not isinstance(e, Edge):
                raise FaceListError(edge_list, "Face must be instantiated from a sequence of Edge objects.")
            this_edge_verts = e.verts
            if this_edge_verts[0] not in prev_edge_verts or this_edge_verts[1] not in prev_edge_verts:
                raise FaceListError(edge_list, "Edges must be connected to make face.")
            prev_edge_verts = this_edge_verts
        ## TO DO: Re-write edge check, include stipulation that only two edges can use a vertex
            
        # Everything OK, can assign the edge list now
        self.edges = edge_list
        
        # Calculate, in order, centroid, normal, and radius
        verts_x = list()
        verts_y = list()
        verts_z = list()
        vert_list = set()
        for e in edge_list:
            if e.verts[0] not in vert_list:
                vert_list.append(e.verts[0])
                verts_x.append(e.verts[0].co[0])
                verts_y.append(e.verts[0].co[1])
                verts_z.append(e.verts[0].co[2])
            if e.verts[1] not in vert_list:
                vert_list.append(e.verts[1])
                verts_x.append(e.verts[1].co[0])
                verts_y.append(e.verts[1].co[1])
                verts_z.append(e.verts[1].co[2])
                
        # This assumes polygon is a triangle
        center_x = 1/3 * fsum(verts_x)
        center_y = 1/3 * fsum(verts_y)
        center_z = 1/3 * fsum(verts_z)
        self.center = vector(center_x, center_y, center_z)
        
        normal_x = 0.0
        normal_y = 0.0
        normal_z = 0.0
        num_verts = len(vert_list)
        for i in range(num_verts):
            normal_x += (verts_y[i] - verts_y[(i + 1) % num_verts]) * (verts_z[i] - verts_z[(i + 1) % num_verts])
            normal_y += (verts_z[i] - verts_z[(i + 1) % num_verts]) * (verts_x[i] - verts_x[(i + 1) % num_verts])
            normal_z += (verts_x[i] - verts_x[(i + 1) % num_verts]) * (verts_y[i] - verts_y[(i + 1) % num_verts])
        self.normal = vector(normal_x, normal_y, normal_z)
        
        c_dist = list()
        for i in range(num_verts):
            c_dist.append(sqrt((self.center[0] - verts_x[i]) ** 2 + (self.center[1] - verts_y[i]) ** 2 + (self.center[2] - verts_z[i]) ** 2))
        self.radius = max(c_dist)
        
        self.vert_norms = [0, 0, 0]     # indexed into Mesh.fvi
        
    def __eq__(self, other):
        if self.edges == other.edges:
            return True
        else:
            return False
            
    def __hash__(self):
        return self.edges
        
    def __repr__(self):
        return "<volition.Face object with edges {}>".format(str(self.edges))
        
    def __str__(self):
        return str(self.edges)
            
## POF chunks ##

class POFChunk:
    """Base class for all POF chunks.  Calling len() on a chunk will return the estimated size of the packed binary chunk, minus chunk header."""
    
    def __init__(self, pof_ver = 2117):
        self.pof_ver = pof_ver
        
class HeaderChunk(POFChunk):

    """POF file header chunk.  Defines various metadata about the model.
    
    Methods:
        read_chunk(bin_data) - takes any Python file object or RawData object and attempts to parse it.  Assumes the chunk header (the chunk ID and length) is NOT included and does not size checking.  Returns True if successful.
        write_chunk() - attempts to pack the data in the chunk into a bytes object, which is returned.  This method DOES include the chunk ID and length in the returned data."""
    
    def __init__(self, pof_ver = 2117):
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
            self.num_cross_sections = unpack_int(bin_data.read(4))
            cross_section_depth = list()
            cross_section_radius = list()
            for i in range(self.num_cross_sections):
                cross_section_depth.append(unpack_float(bin_data.read(4)))
                cross_section_radius.append(unpack_float(bin_data.read(4)))
            self.cross_section_depth = cross_section_depth
            self.cross_section_radius = cross_section_radius
        
        if self.pof_ver >= 2007:
            self.num_lights = unpack_int(bin_data.read(4))
            light_location = list()
            light_type = list()
            for i in range(self.num_lights):
                light_location.append(unpack_vector(bin_data.read(12)))
                light_type.append(unpack_int(bin_data.read(4)))
            self.light_locations = light_location
            self.light_types = light_type
                
        return True
        
    def write_chunk(self):
        
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False
        
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
            chunk += pack_int(self.num_cross_sections)
            cross_section_depth = self.cross_section_depth
            cross_section_radius = self.cross_section_radius
            for i in range(self.num_cross_sections):
                chunk += pack_float(cross_section_depth[i])
                chunk += pack_float(cross_section_radius[i])
                
        if self.pof_ver >= 2007
            chunk += pack_int(self.num_lights)
            light_locations = self.light_locations
            light_types = self.light_types
            for i in range(self.num_lights):
                chunk += pack_float(light_locations[i])
                chunk += pack_int(light_types[i])
        
        return chunk
        
    def __len__(self):
        # Could cause trouble if required POF data isn't actually defined,
        # in which case, WHY ARE YOU TRYING TO WRITE A POF FILE?!
        chunk_length = 44        # Chunk Size
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
                chunk_length += 4 + self.num_cross_sections * 8
        except AttributeError:
            pass
        try:
            if self.light_location:
                chunk_length += 4 + self.num_lights * 16
        except AttributeError:
            pass
        return chunk_length
        
class TextureChunk(POFChunk):
    CHUNK_ID = b'TXTR'
    def read_chunk(self, bin_data):
        self.num_textures = unpack_int(bin_data.read(4))
        textures = list()
        for i in range(self.num_textures):
            str_len = unpack_int(bin_data.read(4))
            textures.append(bin_data.read(str_len))
        self.textures = textures
            
        return True
        
    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False
        
        chunk += pack_int(self.num_textures)
        
        textures = self.textures
        for s in textures:
            chunk += pack_int(len(s))
            chunk += s
            
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
        self.lines = bin_data
        
        return True
        
    def write_chunk(self)
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False
        
        chunk += self.lines
        
        return chunk
        
    def __len__(self):
        try:
            return len(self.lines)
        except AttributeError:
            return 0
            
class PathChunk(POFChunk):
    CHUNK_ID = b'PATH'
    def read_chunk(self, bin_data):
        self.num_paths = unpack_int(bin_data.read(4))
        
        path_names = list()
        path_parents = list()
        num_verts = list()
        vert_pos = list()
        vert_rad = list()
        vert_num_turrets = list()
        turret_sobj_num = list()
        
        for i in range(self.num_paths):
            str_len = unpack_int(bin_data.read(4))
            path_names.append(bin_data.read(str_len))
            
            str_len = unpack_int(bin_data.read(4))
            path_parents.append(bin_data.read(str_len))
            
            num_verts.append(unpack_int(bin_data.read(4)))
            
            vert_pos.append(list())
            vert_rad.append(list())
            vert_num_turrets.append(list())
            turret_sobj_num.append(list())
            
            for j in range(num_verts[i]):
                vert_pos[i].append(unpack_vector(bin_data.read(12)))
                vert_rad[i].append(unpack_float(bin_data.read(4)))
                vert_num_turrets[i].append(unpack_int(bin_data.read(4)))
                
                turret_sobj_num[i].append(list())
                
                for k in range(vert_num_turrets[i][j]):
                    self.turret_sobj_num[i][j].append(unpack_int(bin_data.read(4)))
                    
        self.path_names = path_names
        self.path_parents = path_parents
        self.num_verts = num_verts
        self.vert_pos = vert_pos
        self.vert_rad = vert_rad
        self.vert_num_turrets = vert_num_turrets
        self.turret_sobj_num = turret_sobj_num
                    
        return True
                    
    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False
        
        chunk += pack_int(self.num_paths)
        
        path_names = self.path_names
        path_parents = self.path_parents
        num_verts = self.num_verts
        vert_pos = self.vert_pos
        vert_rad = self.vert_rad
        vert_num_turrets = self.vert_num_turrets
        turret_sobj_num = self.turret_sobj_num
        
        for i in range(self.num_paths):
            chunk += pack_int(len(path_names[i]))
            chunk += path_names[i]
            
            chunk += pack_int(len(path_parents[i]))
            chunk += path_parents[i]
            
            chunk += pack_int(num_verts[i])
            
            for j in range(num_verts[i]):
                chunk += pack_float(vert_pos[i][j])
                chunk += pack_float(vert_rad[i][j])
                chunk += pack_int(vert_num_turrets[i][j])
                
                for k in range(vert_num_turrets[i][j]):
                    chunk += pack_int(sobj_number[i][j][k])
                    
        return chunk
        
    def __len__(self):
        try:
            chunk_length = 4
            
            path_names = self.path_names
            path_parents = self.path_parents
            num_verts = self.num_verts
            vert_num_turrets = self.vert_num_turrets
            
            for i in range(self.num_paths):
                chunk_length += 4 + len(path_names[i])
                chunk_length += 4 + len(path_parents[i])
                chunk_length += 4
                
                for j in range(num_verts[i]):
                    chunk_length += 20
                    chunk_length += 4 * vert_num_turrets[i][j]
                    
            return chunk_length
        except AttributeError:
            return 0
            
class SpecialChunk(POFChunk):
    ## TO DO: Localize variables
    CHUNK_ID = b'SPCL'
    def read_chunk(self, bin_data):
        self.num_special_points = unpack_int(bin_data.read(4))
        
        self.point_names = list()
        self.point_properties = list()
        self.points = list()
        self.point_radius = list()
        
        for i in range(self.num_special_points):
            str_len = unpack_int(bin_data.read(4))
            self.point_names.append(bin_data.read(str_len))
            
            str_len = unpack_int(bin_data.read(4))
            self.point_properties.append(bin_data.read(str_len))
            
            self.points.append(unpack_vector(bin_data.read(12)))
            self.point_radius.append(unpack_float(bin_data.read(4)))
            
        return True
        
    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False
        
        chunk += pack_int(self.num_special_points)
        
        for i in range(self.num_special_points):
            chunk += pack_int(len(self.point_names[i]))
            chunk += self.point_names[i]
            
            chunk += pack_int(len(self.point_properties[i]))
            chunk += self.point_properties[i]
            
            chunk += pack_float(self.points[i])
            chunk += pack_float(self.point_radius[i])
            
        return chunk
        
    def __len__(self):
        try:
            chunk_length = 4
            
            for i in range(self.num_special_points):
                chunk_length += 4 + len(self.point_names[i])
                chunk_length += 4 + len(self.point_properties[i])
                chunk_length += 16
            
            return chunk_length
        except AttributeError:
            return 0
            
class ShieldChunk(POFChunk):
    ## TO DO: Localize variables
    CHUNK_ID = b'SHLD'
    def read_chunk(self, bin_data):
        self.num_verts = unpack_int(bin_data.read(4))
        
        self.vert_pos = list()
        
        for i in range(self.num_verts):
            self.vert_pos.append(unpack_vector(bin_data.read(12)))
            
        self.num_faces = unpack_int(bin_data.read(4))
        
        self.face_normals = list()
        self.face_verts = list()
        self.face_neighbors = list()
        
        for i in range(self.num_faces):
            self.face_normals.append(unpack_vector(bin_data.read(12)))
            self.face_verts.append(unpack_int(bin_data.read(12)))
            self.face_neighbors.append(unpack_int(bin_data.read(12)))
            
    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False
            
        chunk += pack_int(self.num_verts)
        
        for i in range(self.num_verts):
            chunk += pack_float(self.vert_pos[i])
            
        chunk += pack_int(self.num_faces)
        
        for i in range(self.num_faces):
            chunk += pack_float(self.face_normals[i])
            chunk += pack_int(self.face_verts[i])
            chunk += pack_int(self.face_neighbors[i])
            
        return chunk
        
    def get_mesh(self):
        """Returns a mesh object created from the chunk data."""
        
        shld_mesh = Mesh()
        shld_mesh.set_vert_list(self.vert_pos)
        shld_mesh.set_face_list([self.face_verts, self.face_normals])
        return shld_mesh
        
    def set_mesh(self, m):
        """Creates chunk data from a mesh object."""
        
        self.num_verts = len(m.vert_list)
        self.vert_pos = m.get_vert_list()
        
        self.num_faces = len(m.face_list)
        faces = m.get_face_list()
        self.face_verts = faces[0]
        self.face_normals = faces[1]
        
        efi = m._efi
        fei = m._fei
        
        # I know it looks like a big, ugly, nested loop, but remember that:
        # shield meshes only have 80 faces (length of fei)
        # faces only have 3 edges (length of f1)
        # and edges can only be used by 2 faces (length of efi[e])
        # so this takes almost no time at all
        
        face_neighbors = list()
        for i, f1 in fei:
            face_neighbors.append(list())
            for e in f1:
                for f2 in efi[e]:
                    if f2 != i:
                        face_neighbors[i].append(f2)
                        
        self.face_neighbors = face_neighbors
        
    def __len__(self):
        try:
            chunk_length = 8
            
            chunk_length += 12 * self.num_verts
            chunk_length += 36 * self.num_faces
            
            return chunk_length
        except AttributeError:
            return 0