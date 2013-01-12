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
    # calculate edge_list from face_list
    # calculate vert_list from edge_list
    # calculate seams from vert norms
## Chunks
# SubmodelChunk
    # get_mesh()
    # set_mesh(mesh)
    # make_bsp_tree()
# ShieldCollisionChunk
## POF and BSP functions
# validate_pof()
# make_defpoints()
# make_polylist()
# generate_tree_recursion()


from math import fsum, sqrt
from .bintools import *
from . import VolitionError, FileFormatError
import logging

logging.basicConfig(filename="pof.log", level=logging.DEBUG)


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
        ## TO DO: if face_list and not vert_list and not edge_list, make vert_list and edge_list
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
            
            this_vert_norms = set()
            
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
            evi[i] = set(verts.index(e.verts[0]), verts.index(e.verts[1]))
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
        return hash(self.co)
        
    def __repr__(self):
        return "<pof.Vertex object with coords {}>".format(self.co)
        
    def __str__(self):
        return str(self.co)
            
            
class Edge:
    def __init__(self, verts, seam = True):
        if not isinstance(verts[0], Vertex) or not isinstance(verts[1], Vertex) or len(verts) != 2:
            raise VertListError(verts, "Vertex list for Edge object instantiation must be sequence of two Vertex objects.")
        else:
            self.verts = frozenset(verts)
            self.seam = seam
            self.length = sqrt((verts[1].co[0] - verts[0].co[0]) ** 2 + (verts[1].co[1] - verts[0].co[1]) ** 2 + (verts[1].co[2] - verts[0].co[2]) ** 2)
            
    def __eq__(self, other):
        if self.verts == other.verts:
            return True
        else:
            return False
            
    def __hash__(self):
        return hash(self.verts)
        
    def __repr__(self):
        return "<pof.Edge object with vertices {}>".format(str(self.verts))
        
    def __str__(self):
        return str(self.verts)
           
           
class Face:
    def __init__(self, edge_list, uv=False):
        try:
            prev_edge_verts = edge_list[len(edge_list) - 1].verts
        except (AttributeError, ValueError, IndexError, TypeError):
            raise FaceListError(edge_list, "Face must be instantiated from a sequence of Edge objects.")
            
        if uv:
            self.uv = uv
            
        # uv should be a list, indexed into vert_list (created later), of size 2 lists, so that:
        # uv[i][0] is the u coord of list(vert_list)[i]
        # uv[i][1] is the v coord of list(vert_list)[i]
        # etc.
            
        for e in edge_list:
            if not isinstance(e, Edge):
                raise FaceListError(edge_list, "Face must be instantiated from a sequence of Edge objects.")
            this_edge_verts = e.verts
            if this_edge_verts[0] not in prev_edge_verts or this_edge_verts[1] not in prev_edge_verts:
                raise FaceListError(edge_list, "Edges must be connected to make face.")
            prev_edge_verts = this_edge_verts
        ## TO DO: Re-write edge check, include stipulation that only two edges can use a vertex
            
        # Everything OK, can assign the edge list now
        self.edges = frozenset(edge_list)
        
        # Calculate, in order, centroid, normal, and radius
        verts_x = list()
        verts_y = list()
        verts_z = list()
        vert_list = set()
        for e in edge_list:
            if e.verts[0] not in vert_list:
                vert_list.add(e.verts[0])
                verts_x.append(e.verts[0].co[0])
                verts_y.append(e.verts[0].co[1])
                verts_z.append(e.verts[0].co[2])
            if e.verts[1] not in vert_list:
                vert_list.add(e.verts[1])
                verts_x.append(e.verts[1].co[0])
                verts_y.append(e.verts[1].co[1])
                verts_z.append(e.verts[1].co[2])
                
        self.vert_list = vert_list
                
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
        return hash(self.edges)
        
    def __repr__(self):
        return "<pof.Face object with edges {}>".format(str(self.edges))
        
    def __str__(self):
        return str(self.edges)
            
            
## POF helpers ##


class POFChunk:
    """Base class for all POF chunks.  Calling len() on a chunk will return the estimated size of the packed binary chunk, minus chunk header."""
    CHUNK_ID = b"PSPO"
    def __init__(self, pof_ver=2117, chunk_id=b'PSPO'):
        self.pof_ver = pof_ver
        
    def __len__(self):
        return 0
        
    def __repr__(self):
        return "<POF chunk with ID {}, size {}, and POF version {}>".format(self.CHUNK_ID, len(self), self.pof_ver)
        
        
## POF chunks and BSP blocks ##
        
        
class HeaderChunk(POFChunk):

    """POF file header chunk.  Defines various metadata about the model.
    
    Methods:
        read_chunk(bin_data) - takes any Python file object or RawData object and attempts to parse it.  Assumes the chunk header (the chunk ID and length) is NOT included and does not size checking.  Returns True if successful.
        write_chunk() - attempts to pack the data in the chunk into a bytes object, which is returned.  This method DOES include the chunk ID and length in the returned data."""
    
    def __init__(self, pof_ver=2117, chunk_id=b'PSPO'):
        self.pof_ver = pof_ver
        if pof_ver >= 2116:
            self.CHUNK_ID = b'HDR2'
        else:
            self.CHUNK_ID = b'OHDR'
            
    def read_chunk(self, bin_data):
        #logging.debug("Reading header chunk...")
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
        # Could cause trouble if required POF data isn't actually defined,
        # in which case, WHY ARE YOU TRYING TO WRITE A POF FILE?!
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
        #logging.debug("Reading texture chunk...")
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
        #logging.debug("Reading PINF chunk...")
        self.lines = bin_data.read().split(b'\0')
        
    def write_chunk(self):
        chunk = self.CHUNK_ID
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False
            
        logging.debug("Writing PINF chunk with size {}...".format(length))
        
        chunk += b"\0".join(self.lines) + b"\0"
        
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
        #logging.debug("Reading path chunk...")
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
                    self.turret_sobj_num[i][j].append(unpack_int(bin_data.read(4)))
                    
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
        #logging.debug("Reading special point chunk...")
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
    def read_chunk(self, bin_data):
        #logging.debug("Reading shield chunk...")
        num_verts = unpack_int(bin_data.read(4))
        #logging.debug("Number of verts {}".format(num_verts))
        
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
        """Returns a mesh object created from the chunk data."""
        
        shld_mesh = Mesh()
        shld_mesh.set_vert_list(self.vert_list)
        shld_mesh.set_face_list([self.face_list, self.face_normals])
        return shld_mesh
        
    def set_mesh(self, m):
        """Creates chunk data from a mesh object."""
        
        self.num_verts = len(m.vert_list)
        self.vert_list = m.get_vert_list()
        
        self.num_faces = len(m.face_list)
        faces = m.get_face_list()
        self.face_list = faces[0]
        self.face_normals = faces[1]
        
        efi = m._efi
        fei = m._fei
        
        # I know it looks like a big, ugly, nested loop, but remember that:
        # shield meshes only have 80 faces (length of fei)
        # faces only have 3 edges (length of f1)
        # and edges can only be used by 2 faces (length of efi[e])
        # that makes only 480 iterations,
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
            
            chunk_length += 12 * len(self.vert_list)
            chunk_length += 36 * len(self.face_list)
            
            return chunk_length
        except AttributeError:
            return 0
            
            
class EyeChunk(POFChunk):
    CHUNK_ID = b" EYE"
    def read_chunk(self, bin_data):
        #logging.debug("Reading eye chunk...")
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
        #logging.debug("Reading gun point chunk...")
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
        #logging.debug("Reading turret chunk...")
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
                firing_points[i].append(unpack_int(bin_data.read(4)))
                
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
        num_firing_points = self.num_firing_points
        firing_points = self.firing_points
        
        num_banks = len(firing_points)
        chunk += pack_int(num_banks)
        
        for i in range(self.num_banks):
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
        #logging.debug("Reading dock chunk...")
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
        #logging.debug("Reading thruster chunk...")
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
                #logging.debug("{} {}".format(block_id, block_size))
                #logging.debug("BSP block ID {} with size {}".format(block_id, block_size))
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
            #logging.debug("{} {}".format(block.CHUNK_ID, len(block)))
            bsp_data += block.write_chunk()
            
        logging.debug("And BSP data size {}...".format(len(bsp_data)))
        chunk += pack_int(len(bsp_data))
        chunk += bsp_data
        
        return chunk
        
    def get_mesh(self):
        pass
        
    def set_mesh(self, m):
        # Basically:
        # defpoints = DefpointsBlock()
        # defpoints.set_mesh(m)
        # self._defpoints = defpoints
        # polylist = self._make_polylist(m)
        # self._polylist = polylist
        # self._generate_tree_recursion()
        # self.bsp_tree = self._defpoints + self._polylist
        pass
        
    def _generate_tree_recursion(self):
        pass
        
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
        #logging.debug("Reading insignia chunk...")
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
        #logging.debug("Reading autocenter chunk...")
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
        #logging.debug("Reading glowpoint chunk...")
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
            if node_type:
                this_node = ShieldLeaf()
                this_node.min = unpack_vector(bin_data.read(12))
                this_node.max = unpack_vector(bin_data.read(12))
                this_node.front = unpack_uint(bin_data.read(4))
                this_node.back = unpack_uint(bin_data.read(4))
            else:
                this_node = ShieldSplit()
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
        logging.debug("Writing shield collision tree with size {}...".format(len(self)))
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
        
    def make_shield_collision_tree(self, shield_chunk):
        pass
        
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
    front_offset = None
    back_offset = None
    
    def __len__(self):
        return 32
    
    
class ShieldLeaf:
    node_type = 1
    min = None
    max = None
    face_list = list()
    
    def __len__(self):
        return 28 + 4 * len(self.face_list)
        

class EndBlock(POFChunk):
    CHUNK_ID = 0
    def read_chunk(self, bin_data):
        pass
        
    def write_chunk(self):
        return b"\0\0\0\0\0\0\0\0"
        
    def __len__(self):
        return 0

        
class DefpointsBlock(POFChunk):
    CHUNK_ID = 1
    def read_chunk(self, bin_data):
        #logging.debug("Found Defpoints")
        num_verts = unpack_int(bin_data.read(4))
        #logging.debug("Number of verts {}".format(num_verts))
        num_norms = unpack_int(bin_data.read(4))
        #logging.debug("Number of normals {}".format(num_norms))
        vert_data_offset = unpack_int(bin_data.read(4))
        #logging.debug("Vert data offset {} bytes".format(vert_data_offset))
        
        norm_counts = list()
        
        for i in range(num_verts):
            norm_counts.append(unpack_byte(bin_data.read(1)))
            
        #logging.debug("Norm counts \n{}".format(norm_counts))
            
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
                
        #logging.debug("Vert list \n{}".format(vert_list))
        #logging.debug("Vert norms \n{}".format(vert_norms))
                
        self.vert_list = vert_list
        self.vert_norms = vert_norms
        
    def write_chunk(self):
        chunk = pack_int(self.CHUNK_ID)
        length = len(self)
        if length:
            chunk += pack_int(length)
        else:
            return False
            
        #logging.debug("Writing Defpoints")
            
        vert_list = self.vert_list
        vert_norms = self.vert_norms
        num_verts = len(vert_list)
        num_norms = 0
        vert_data_offset = 20 + num_verts
        
        for v in vert_norms:
            num_norms += len(v)
            
        #logging.debug("Number of verts {}".format(num_verts))
        #logging.debug("Number of norms {}".format(num_norms))
        #logging.debug("Vert data offset {}".format(vert_data_offset))
        
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
        m.set_vert_list(self.vert_list, self.vert_norms)
        
        return m
                
    def set_mesh(self, m):
        vert_list = m.get_vert_list()
        vert_norms = list()
        for v in m.vert_list:
            vert_norms.append(v.normals)
            
        self.vert_list = vert_list
        self.vert_norms = vert_norms
        
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
            
        self.vert_list = vert_list
        self.norm_list = norm_list
        
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
        chunk += pack_int(len(self.vert_list))
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
            
    return chunk_list
    
    
def write_pof(chunk_list, pof_version=2117):
    """Takes a list of chunks as a required argument, returns a bytes object.  Optional argument pof_version specifies
    the POF version (duh).  If any chunk does not use the same version as used for the file, the file might not be
    valid and readable!"""
    
    logging.info("Attempting to create POF file from chunk list...")
    
    pof_file = b"".join([b'PSPO', pack_int(pof_version)])
    
    for chunk in chunk_list:
        pof_file += chunk.write_chunk()
        
    return pof_file

   