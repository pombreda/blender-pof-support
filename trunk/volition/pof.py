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
        return "Invalid filetype: {}, {}.".format(self.msg, self.path)
        
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
        get_edge_list() - parses self.edge_list and returns a list in the format [[u0, v0, s0], [u1, v1, s1], ...], where ui and vi are indexed into self.vert_list and sx is the boolean seam value
        set_edge_list(edge_list) - parses a list in the same format as returned by get_edge_list() to self.edge_list
        get_face_list(by_edges = False) - parses self.face_list and returns a list in the format [[vert_idx], [face_norms]] or, if by_edges is True, [[edge_idx], [face_norms]]
        set_face_list(face_list, vert_norms = False, by_edges = False) - parses a list in the same format as returned by get_face_list() to self.face_list
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
    
        ## TO DO: Localize self.face_list, self.vert_list, self.edge_list
    
        vert_list = list()
        for v in self.vert_list:
            vert_list.append(v.co)
            
        return vert_list
        
    def set_vert_list(self, vert_list, vert_norms = False):
    
        ## TO DO: Localize self.face_list, self.vert_list, self.edge_list
    
        self.vert_list = list()
        for i in range(len(vert_list)):
            self.vert_list.append(Vertex(vert_list[i]))
            if vert_norms:
                self.vert_list[i].normals = vert_norms[i]
                
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
    
        ## TO DO: Localize self.face_list, self.vert_list, self.edge_list
    
        edge_list = list()
        for i in range(len(self.edge_list)):
            edge_list.append(list())
            edge_list[i].append(self.vert_list.index(self.edge_list[i].verts[0]))
            edge_list[i].append(self.vert_list.index(self.edge_list[i].verts[1]))
            edge_list[i].append(self.edge_list[i].seam)
            
        return edge_list
        
    def set_edge_list(self, edge_list):
    
        ## TO DO: Localize self.face_list, self.vert_list, self.edge_list
    
        self.edge_list = list()
        for e in edge_list:
            self.edge_list.append(Edge(e[:2], e[2]))
            
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
    
        ## TO DO: Localize self.face_list, self.vert_list, self.edge_list
    
        face_list = [[], []]
        for i in range(len(self.face_list)):
            face_list[0].append(list())
            if by_edges:
                for j in range(len(self.face_list[i].edges)):
                    face_list[0][i].append(self.edge_list.index(self.face_list[i].edges[j]))
            else:
                for e in self.face_list[i].edges:
                    vert_idx = self.vert_list.index(e.verts[0])
                    if vert_idx not in face_list[0][i]:
                        face_list[0][i].append(vert_idx)
                    vert_idx = self.vert_list.index(e.verts[1])
                    if vert_idx not in face_list[0][i]:
                        face_list[0][i].append(vert_idx)
            face_list[1].append(self.face_list[i].normal)
            
        return face_list
        
    def set_face_list(self, face_list, vert_norms = False, by_edges = False):
    
        ## TO DO: Localize self.face_list, self.vert_list, self.edge_list
        
        self.face_list = list()
        if by_edges:
            for i in range(len(face_list[0])):
                edge_list = list()
                for e in face_list[0][i]:
                    edge_list.append(self.edge_list[e])
                self.face_list.append(Face(edge_list))
        else:   # go through vert list, make edges
                # assumes mesh is fully triangulated
            for i in range(len(face_list[0])):
                try:
                    edge_a = self.edge_list[index(Edge(self.vert_list[face_list[0][i][0]], self.vert_list[face_list[0][i][1]]))]
                except ValueError:  # Edge doesn't exist in self.edge_list, so we need to add it
                    edge_a = Edge(self.vert_list[face_list[0][i][0]], self.vert_list[face_list[0][i][1]])
                    self.edge_list.append(edge_a)
                try:
                    edge_b = self.edge_list[index(Edge(self.vert_list[face_list[0][i][1]], self.vert_list[face_list[0][i][2]]))]
                except ValueError:
                    edge_b = Edge(self.vert_list[face_list[0][i][1]], self.vert_list[face_list[0][i][2]])
                    self.edge_list.append(edge_b)
                try:
                    edge_c = self.edge_list[index(Edge(self.vert_list[face_list[0][i][2]], self.vert_list[face_list[0][i][0]]))]
                except ValueError:
                    edge_c = Edge(self.vert_list[face_list[0][i][2]], self.vert_list[face_list[0][i][0]])
                    self.edge_list.append(edge_c)
                    
                # making this more complicated than it needs to be so that all the faces in self.face_list reference edges in self.edge_list
                self.face_list.append(Face([self.edge_list[self.edge_list.index(edge_a)], self.edge_list[self.edge_list.index(edge_b)], self.edge_list[self.edge_list.index(edge_c)]]))
                # the pont being that if we modify, say, the position of a vertex, the change will be reflected in the edges and faces, too.
                # Why?  I dunno, maybe you want to make a script that will flip the model's x-axis?  Then just flip the x-axis of all the vertices and the edges and faces will follow.
                
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
        
        for i in len(faces):        
            fe = set()     # list of indices
            fv = set()      # set of indices
            for e in faces[i].edges:
                fe.add(edges.index(e))
                fv.add(verts.index(e.verts[0]), verts.index(e.verts[1]))
            fei[i] = fe
            fvi[i] = fv
            
        for i in len(edges):
            evi[i] = set(verts.index(edges[i].verts[0]), verts.index(edges[i].verts[1])
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
        
        for i in len(faces):        
            fe = set()     # list of indices
            fv = set()      # set of indices
            for e in faces[i].edges:
                fe.add(edges.index(e))
                fv.add(verts.index(e.verts[0]), verts.index(e.verts[1]))
            fei[i] = fe
            fvi[i] = fv
            
        for i in len(edges):
            evi[i] = set(verts.index(edges[i].verts[0]), verts.index(edges[i].verts[1])
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
            
class Edge:
    def __init__(self, verts, seam = True):
        if not isinstance(verts[0], Vertex) or not isinstance(verts[1], Vertex) or len(verts) != 2:
            raise VertListError(verts, "Vertex list for Edge object instantiation must be sequence of two Vertex objects.")
        else:
            self.verts = verts
            self.seam = seam
            self.length = sqrt((verts[1].co[0] - verts[0].co[0]) ** 2 + (verts[1].co[1] - verts[0].co[1]) ** 2 + (verts[1].co[2] - verts[0].co[2]) ** 2)
            
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
        vert_list = list()
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
        ## TO DO: calculate centroid for arbitrary polygon
        center_x = 1/3 * fsum(verts_x)
        center_y = 1/3 * fsum(verts_y)
        center_z = 1/3 * fsum(verts_z)
        self.center = vector(center_x, center_y, center_z)
        
        normal_x = 0.0
        normal_y = 0.0
        normal_z = 0.0
        for i in range(len(vert_list)):
            normal_x += (verts_y[i] - verts_y[(i + 1) % len(verts_y)]) * (verts_z[i] - verts_z[(i + 1) % len(verts_z)])
            normal_y += (verts_z[i] - verts_z[(i + 1) % len(verts_z)]) * (verts_x[i] - verts_x[(i + 1) % len(verts_x)])
            normal_z += (verts_x[i] - verts_x[(i + 1) % len(verts_x)]) * (verts_y[i] - verts_y[(i + 1) % len(verts_y)])
        self.normal = vector(normal_x, normal_y, normal_z)
        
        c_dist = list()
        for i in range(len(vert_list)):
            c_dist.append(sqrt((self.center[0] - verts_x[i]) ** 2 + (self.center[1] - verts_y[i]) ** 2 + (self.center[2] - verts_z[i]) ** 2))
        self.radius = max(c_dist)
        
        self.vert_norms = [0, 0, 0]     # indexed into Mesh.fvi
            
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
        self.sobj_detail_levels = list()
        for i in range(self.num_detail_levels):
            self.sobj_detail_levels.append(unpack_int(bin_data.read(4)))
            
        self.num_debris = unpack_int(bin_data.read(4))
        self.sobj_debris = list()
        for i in range(self.num_debris):
            self.sobj_debris.append(unpack_int(bin_data.read(4)))
            
        if self.pof_ver >= 1903:
            self.mass = unpack_float(bin_data.read(4))
            self.mass_center = unpack_vector(bin_data.read(12))
            self.inertia_tensor = list()
            for i in range(3):
                self.inertia_tensor.append(list())
                for j in range(3):
                    self.inertia_tensor[i].append(unpack_float(bin_data.read(4)))
        
        if self.pof_ver >= 2014:
            self.num_cross_sections = unpack_int(bin_data.read(4))
            self.cross_section_depth = list()
            self.cross_section_radius = list()
            for i in range(self.num_cross_sections):
                self.cross_section_depth.append(unpack_float(bin_data.read(4)))
                self.cross_section_radius.append(unpack_float(bin_data.read(4)))
        
        if self.pof_ver >= 2007:
            self.num_lights = unpack_int(bin_data.read(4))
            self.light_location = list()
            self.light_type = list()
            for i in range(self.num_lights):
                self.light_location.append(unpack_vector(bin_data.read(12)))
                self.light_type.append(unpack_int(bin_data.read(4)))
                
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
            for i in self.moment_inertia:
                chunk += pack_float(i)
                
        if self.pof_ver >= 2014:
            chunk += pack_int(self.num_cross_sections)
            for i in range(self.num_cross_sections):
                chunk += pack_float(self.cross_section_depth)
                chunk += pack_float(self.cross_section_radius)
                
        if self.pof_ver >= 2007
            chunk += pack_int(self.num_lights)
            for i in range(self.num_lights):
                chunk += pack_float(self.light_location)
                chunk += pack_int(self.light_type)
        
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
        self.textures = list()
        for i in range(self.num_textures):
            str_len = unpack_int(bin_data.read(4))
            self.textures.append(bin_data.read(str_len))
            
        return True
        
    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False
        
        chunk += pack_int(self.num_textures)
        
        for s in self.textures:
            chunk += pack_int(len(s))
            chunk += s
            
        return chunk
        
    def __len__(self):
        try:
            chunk_length = 4
            for s in self.textures:
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
        
        self.path_names = list()
        self.path_parents = list()
        self.num_verts = list()
        self.vert_pos = list()
        self.vert_rad = list()
        self.vert_num_turrets = list()
        self.turret_sobj_num = list()
        
        for i in range(self.num_paths):
            str_len = unpack_int(bin_data.read(4))
            self.path_names.append(bin_data.read(str_len))
            
            str_len = unpack_int(bin_data.read(4))
            self.path_parents.append(bin_data.read(str_len))
            
            self.num_verts.append(unpack_int(bin_data.read(4)))
            
            self.vert_pos.append(list())
            self.vert_rad.append(list())
            self.vert_num_turrets.append(list())
            self.turret_sobj_num.append(list())
            
            for j in range(self.num_verts[i]):
                self.vert_pos[i].append(unpack_vector(bin_data.read(12)))
                self.vert_rad[i].append(unpack_float(bin_data.read(4)))
                self.vert_num_turrets[i].append(unpack_int(bin_data.read(4)))
                
                self.turret_sobj_num[i].append(list())
                
                for k in range(self.vert_num_turrets[i][j]):
                    self.turret_sobj_num[i][j].append(unpack_int(bin_data.read(4)))
                    
        return True
                    
    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False
        
        chunk += pack_int(self.num_paths)
        
        for i in range(self.num_paths):
            chunk += pack_int(len(self.path_names[i]))
            chunk += self.path_names[i]
            
            chunk += pack_int(len(self.path_parents[i]))
            chunk += self.path_parents[i]
            
            chunk += pack_int(self.num_verts[i])
            
            for j in range(self.num_verts[i]):
                chunk += pack_float(self.vert_pos[i][j])
                chunk += pack_float(self.vert_rad[i][j])
                chunk += pack_int(self.vert_num_turrets[i][j])
                
                for k in range(self.vert_num_turrets[i][j]):
                    chunk += pack_int(self.sobj_number[i][j][k])
                    
        return chunk
        
    def __len__(self):
        try:
            chunk_length = 4
            
            for i in range(self.num_paths):
                chunk_length += 4 + len(self.path_names[i])
                chunk_length += 4 + len(self.path_parents[i])
                chunk_length += 4
                
                for j in range(self.num_verts[i]):
                    chunk_length += 20
                    chunk_length += 4 * self.vert_num_turrets[i][j]
                    
            return chunk_length
        except AttributeError:
            return 0
            
class SpecialChunk(POFChunk):
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
        
    def __len__(self):
        try:
            chunk_length = 8
            
            chunk_length += 12 * self.num_verts
            chunk_length += 36 * self.num_faces
            
            return chunk_length
        except AttributeError:
            return 0