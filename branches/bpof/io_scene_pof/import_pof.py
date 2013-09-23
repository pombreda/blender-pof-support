# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
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

"""
This script imports Volition POF files to Blender.

Usage:
Run this script from "File->Import" menu and then load the desired POF file.

http://code.google.com/p/blender-pof-support/wiki/ImportScript
"""


import os
import time
import bpy
import mathutils
from bpy_extras.io_utils import unpack_list, unpack_face_list
from . import pof


## For texturing:
# In load(), make material for each texture
# In create_mesh(), make ONE uv layer, assign materials per face
# For a given mesh, all textures (materials) take their coords from a single
# active UV layer.  All you have to do is assign each face a material.


def create_mesh(sobj, use_smooth_groups, fore_is_y, import_textures):
    """Takes a submodel and adds a Blender mesh."""
    m = sobj.get_mesh()
    
    if fore_is_y:
        m.flip_yz()

    me = bpy.data.meshes.new("{}-mesh".format(sobj.name.decode()))

    vert_list = m.verts
    face_list = m.faces
    me.vertices.add(len(vert_list))
    me.vertices.foreach_set('co', unpack_list(vert_list))
    me.tessfaces.add(len(face_list))
    me.tessfaces.foreach_set('vertices_raw', unpack_face_list(face_list))

    invisible_faces = 0

    if import_textures:
        m.flip_v()
        uvtex = me.tessface_uv_textures.new()
        uvtex.name = me.name
        for n, tf in enumerate(m.uv):
            uv_data = uvtex.data[n]
            uv_data.uv1 = tf[0]
            uv_data.uv2 = tf[1]
            uv_data.uv3 = tf[2]
            if len(tf) == 4:
                uv_data.uv4 = tf[3]
            if m.tex_ids[n] is not None:
                tex_slot = import_textures[m.tex_ids[n]].texture_slots[0]
            else:
                tex_slot = None
            if tex_slot is not None:
                uv_data.image = tex_slot.texture.image
            else:
                invisible_faces += 1
        for mat in import_textures:
            me.materials.append(mat)
        for i, f in enumerate(me.tessfaces):
            if m.tex_ids[n] is not None:
                f.material_index = m.tex_ids[i]
        uvtex.active = True
        uvtex.active_render = True

    # index edges in a dict by a frozenset of the vert coords
    # that way we don't have to worry about messed up indicies when
    # adding the seams for smoothgroups (an edge might be [v1, v2] or [v2, v1])
    me.update(calc_edges=True)
    if use_smooth_groups:
        m.calc_sharp()
        for e in me.edges:
            v1 = tuple(me.vertices[e.vertices[0]].co)
            v2 = tuple(me.vertices[e.vertices[1]].co)
            this_edge = (v1, v2)
            this_edge = frozenset(this_edge)
            e.use_edge_sharp = m.edges[this_edge]
        for f in me.polygons:
            f.use_smooth = True

    bobj = bpy.data.objects.new("Mesh", me)
    bobj['POF model id'] = sobj.model_id
    bobj.name = sobj.name.decode()
    if use_smooth_groups:
        bobj.modifiers.new("POF smoothing", "EDGE_SPLIT")
    if invisible_faces > 2 * (len(me.polygons) / 3):
        bobj.draw_type = 'WIRE'
        
    return bobj


def load(operator, context, filepath,
        use_smooth_groups=False,
        import_eye_points=True,
        import_paths=True,
        import_gun_points=True,
        import_mis_points=True,
        import_tgun_points=True,
        import_tmis_points=True,
        import_thrusters=True,
        import_glow_points=True,
        #import_flash_points=True,
        import_special_points=True,
        import_header_data=True,
        import_only_main=False,
        import_detail_levels=True,
        import_detail_boxes=True,
        import_debris=True,
        import_turrets=True,
        import_specials=True,
        #import_special_debris=True,
        fore_is_y=True,
        import_shields=True,
        import_textures=False,
        texture_path="/../maps/",
        texture_format=".dds",
        pretty_materials=False
        ):
    
    print("\tloading POF file {}...".format(filepath))
    filepath = os.fsencode(filepath)
    cur_time = time.time()
    pof_file = open(filepath, 'rb')
    pof_handler = pof.read_pof(pof_file)
    pof_file.close()
    new_time = time.time()
    print("\ttime to load POF handler {} sec".format(new_time - cur_time))

    # we now have a PolyModel instance containing all the chunks
    # now we check through the kwargs and call the appropriate
    # methods to read the PolyModel

    if pof_handler.pof_ver >= 2116:
        pof_hdr = pof_handler.chunks["HDR2"]
    else:
        pof_hdr = pof_handler.chunks["OHDR"]

    scene = context.scene

    cur_time = time.time()

    # Textures first

    # we'll do this by making a material for every texture
    # if we're importing pretty textures, we'll make a
    # Blender texture each for shine, normal, glow, etc.
    
    # we'll keep the materials in a list and link every material
    # to every submodel object.  That way, we can assign
    # material indices that are the same as the POF texture indices

    # get an absolute path for textures
    texture_path = bytes(texture_path, 'UTF-8')
    texture_format = bytes(texture_format, 'UTF-8')
    texture_path = os.path.normpath(os.path.dirname(filepath) + texture_path)
    print(texture_path)

    if not os.path.isdir(texture_path):
        print("Given texture path is not a valid directory.")
        import_textures = False

    if import_textures:
        txtr_chunk = pof_handler.chunks["TXTR"]
        # go through txtr_chunk, make Blender images for each
        # if pretty_textures: get shine, normal, glow, etc., too
        missing_textures = 0
        bmats = list()
        bimgs = list()
        if pretty_materials:
            shine_imgs = list()
            norm_imgs = list()
            glow_imgs = list()
        for tex in txtr_chunk.textures:
            tex_path = os.path.join(texture_path, tex + texture_format)
            if os.path.isfile(tex_path):
                bimgs.append(bpy.data.images.load(tex_path))
            elif tex == b'invisible':
                bimgs.append(None)
            else:
                print("Missing texture {}".format(tex))
                bimgs.append(None)
                missing_textures += 1
            if pretty_materials:
                shine_name = tex + b"-shine" + texture_format
                norm_name = tex + b"-normal" + texture_format
                glow_name = tex + b"-glow" + texture_format
                shine_path = os.path.join(texture_path, shine_name)
                norm_path = os.path.join(texture_path, norm_name)
                glow_path = os.path.join(texture_path, glow_name)
                if os.path.isfile(shine_path):
                    shine_imgs.append(bpy.data.images.load(shine_path))
                else:
                    shine_imgs.append(None)
                    print("Missing texture {}".format(shine_path))
                    missing_textures += 1
                if os.path.isfile(norm_path):
                    norm_imgs.append(bpy.data.images.load(norm_path))
                else:
                    norm_imgs.append(None)
                    print("Missing texture {}".format(norm_path))
                    missing_textures += 1
                if os.path.isfile(glow_path):
                    glow_imgs.append(bpy.data.images.load(glow_path))
                else:
                    glow_imgs.append(None)
                    print("Missing texture {}".format(glow_path))
                    missing_textures += 1
        print("Total missing textures: {}".format(missing_textures))
        #if missing_textures > 0:    # change this later
            #import_textures = False

    # Create a material for each texture listed in the chunk
    # Each object has its own UV layer with the base texture
    # In addition to the UV layer, the material must have a
    # texture slot with the image, set to UV coordinates
    # if using pretty materials, then we need additional
    # texture slots with the other maps, same UV layer for coords
    # We do NOT need a material for each object as long as
    # each object's UV layer has the same name

    if import_textures:
        # for each img, make a texture and material
        bmats = list()
        for i, img in enumerate(bimgs):
            if img is None:
                this_mat = bpy.data.materials.new('invisible')
                this_mat.alpha = 1.0
                this_mat.use_transparency = True
            else:
                this_txtr = bpy.data.textures.new(img.name + '-txtr', type='IMAGE')
                this_txtr.image = img
                this_txtr.use_alpha = True
                this_mat = bpy.data.materials.new(img.name + '-mat')
                mat_txtr = this_mat.texture_slots.add()
                mat_txtr.texture = this_txtr
                mat_txtr.texture_coords = 'UV'
                mat_txtr.use_map_color_diffuse = True
                mat_txtr.use_map_alpha = True
                mat_txtr.use = True

                if pretty_materials:
                    if shine_imgs[i] is not None:
                        this_shine = bpy.data.textures.new(shine_imgs[i].name + '-txtr', type='IMAGE')
                        this_shine.image = shine_imgs[i]
                        #this_shine.use_alpha = True
                        mat_shine = this_mat.texture_slots.add()
                        mat_shine.texture = this_shine
                        mat_shine.texture_coords = 'UV'
                        mat_shine.use_map_specular = True
                        mat_shine.use_map_color_diffuse = False
                        mat_shine.use = True

                    if norm_imgs[i] is not None:
                        this_norm = bpy.data.textures.new(norm_imgs[i].name + '-txtr', type='IMAGE')
                        this_norm.image = norm_imgs[i]
                        #this_norm.use_alpha = True
                        this_norm.use_normal_map = True
                        mat_norm = this_mat.texture_slots.add()
                        mat_norm.texture = this_norm
                        mat_norm.texture_coords = 'UV'
                        mat_norm.use_map_normal = True
                        mat_norm.normal_factor = 0.4
                        mat_norm.use_map_color_diffuse = False
                        mat_norm.use = True

                    if glow_imgs[i] is not None:
                        this_glow = bpy.data.textures.new(glow_imgs[i].name + '-txtr', type='IMAGE')
                        this_glow.image = glow_imgs[i]
                        this_glow.use_alpha = False
                        mat_glow = this_mat.texture_slots.add()
                        mat_glow.texture = this_glow
                        mat_glow.texture_coords = 'UV'
                        mat_glow.use_map_emit = True
                        #mat_glow.use_map_ambient = True
                        mat_glow.use_map_color_diffuse = True
                        mat_glow.blend_type = 'ADD'
                        mat_glow.use = True

            bmats.append(this_mat)
    else:
        bmats = False

    # Now submodels

    new_objects = dict()    # dict instead of list so
                            # we can ref by POF model id
    # for testing UV mapping:
    #import_textures = True
    if import_only_main:
        # import only first detail level and its children

        # get first detail level
        hull_id = pof_hdr.sobj_detail_levels[0]
        hull = pof_handler.submodels[hull_id]
        hull_obj = create_mesh(hull, use_smooth_groups, fore_is_y, bmats)
        new_objects[hull_id] = hull_obj
        scene.objects.link(hull_obj)

        # get children
        child_ids = dict()
        for model in pof_handler.submodels.values():
            if model.parent_id == hull_id:
                child_obj = create_mesh(model, use_smooth_groups, fore_is_y, bmats)
                child_obj.parent = hull_obj
                if fore_is_y:
                    off_x = model.offset[0]
                    off_y = model.offset[1]
                    off_z = model.offset[2]
                    child_obj.location = (off_x, off_z, off_y)
                else:
                    child_obj.location = model.offset
                new_objects[model.model_id] = child_obj
                scene.objects.link(child_obj)

        # get second children
        for model in pof_handler.submodels.values():
            if model.parent_id in child_ids:
                child_obj = create_mesh(model, use_smooth_groups, fore_is_y, bmats)
                child_obj.parent = new_objects[model.parent_id]
                x_off = pof_handler.submodels[model.parent_id].offset[0] + model.offset[0]
                y_off = pof_handler.submodels[model.parent_id].offset[1] + model.offset[1]
                z_off = pof_handler.submodels[model.parent_id].offset[2] + model.offset[2]
                if fore_is_y:
                    child_obj.location = (x_off, z_off, y_off)
                else:
                    child_obj.location = (x_off, y_off, z_off)
                new_objects[model.model_id] = child_obj
                scene.objects.link(child_obj)

    else:
        layer_count = 0
        #debris_layer = None
        main_detail = None

        if import_detail_levels:
            # TODO get children!
            for i in pof_hdr.sobj_detail_levels:
                model = pof_handler.submodels[i]
                this_obj = create_mesh(model, use_smooth_groups, fore_is_y, bmats)
                # put LODs on sep layers from each other
                new_objects[model.model_id] = this_obj
                scene.objects.link(this_obj)
                this_obj.layers[layer_count] = True
                if layer_count:
                    this_obj.layers[0] = False
                layer_count += 1
            #main_detail = new_objects[0]
            #print(new_objects)

        if import_debris:
            for i in pof_hdr.sobj_debris:
                model = pof_handler.submodels[i]
                this_obj = create_mesh(model, use_smooth_groups, fore_is_y, bmats)
                # put debris on sep layer from LODs, but same as each other
                new_objects[model.model_id] = this_obj
                scene.objects.link(this_obj)
                this_obj.layers[layer_count] = True
                if layer_count:
                    this_obj.layers[0] = False
                #debris_layer = layer_count
            #layer_count += 1

        if import_turrets:
            # TODO add children
            if "TGUN" in pof_handler.chunks:
                tchunk = pof_handler.chunks["TGUN"]
                for i in range(len(tchunk.base_sobj)):
                    model = pof_handler.submodels[tchunk.base_sobj[i]]
                    this_obj = create_mesh(model, use_smooth_groups, fore_is_y, bmats)
                    if main_detail is not None:
                        this_obj.parent = main_detail
                    off_x = model.offset[0]
                    off_y = model.offset[1]
                    off_z = model.offset[2]
                    if fore_is_y:
                        this_obj.location = (off_x, off_z, off_y)
                    else:
                        this_obj.location = (off_x, off_y, off_z)

                    if tchunk.barrel_sobj[i] > -1:
                        bar_model = pof_handler.submodels[tchunk.barrel_sobj[i]]
                        barrel_obj = create_mesh(bar_model, use_smooth_groups, fore_is_y, bmats)
                        barrel_obj.parent = this_obj
                        off_x += model.offset[0]
                        off_y += model.offset[1]
                        off_z += model.offset[2]
                        if fore_is_y:
                            barrel_obj.location = (off_x, off_z, off_y)
                        else:
                            barrel_obj.location = (off_x, off_y, off_z)
                        new_objects[bar_model.model_id] = barrel_obj
                        scene.objects.link(barrel_obj)
                    new_objects[model.model_id] = this_obj
                    scene.objects.link(this_obj)

            if "TMIS" in pof_handler.chunks:
                tchunk = pof_handler.chunks["TMIS"]
                for i in range(len(tchunk.base_sobj)):
                    model = pof_handler.submodels[tchunk.base_sobj[i]]
                    this_obj = create_mesh(model, use_smooth_groups, fore_is_y, bmats)
                    if main_detail is not None:
                        this_obj.parent = main_detail
                    off_x = model.offset[0]
                    off_y = model.offset[1]
                    off_z = model.offset[2]
                    if fore_is_y:
                        this_obj.location = (off_x, off_z, off_y)
                    else:
                        this_obj.location = (off_x, off_y, off_z)

                    if tchunk.barrel_sobj[i] > -1:
                        bar_model = pof_handler.submodels[tchunk.barrel_sobj[i]]
                        barrel_obj = create_mesh(bar_model, use_smooth_groups, fore_is_y, bmats)
                        barrel_obj.parent = this_obj
                        off_x += model.offset[0]
                        off_y += model.offset[1]
                        off_z += model.offset[2]
                        if fore_is_y:
                            barrel_obj.location = (off_x, off_z, off_y)
                        else:
                            barrel_obj.location = (off_x, off_y, off_z)
                        new_objects[bar_model.model_id] = barrel_obj
                        scene.objects.link(barrel_obj)
                    new_objects[model.model_id] = this_obj
                    scene.objects.link(this_obj)

        if import_specials:
            for model in pof_handler.submodels.values():
                if b"subsystem" in model.properties:
                    this_obj = create_mesh(model, use_smooth_groups, fore_is_y, bmats)
                    this_obj.parent = new_objects[model.parent_id]
                    new_objects[model.model_id] = this_obj
                    scene.objects.link(this_obj)

    if import_shields and "SHLD" in pof_handler.chunks:
        model = pof_handler.chunks["SHLD"]
        this_obj = create_mesh(model, False, fore_is_y, False)
        this_obj.draw_type = "WIRE"
        new_objects["shield"] = this_obj
        scene.objects.link(this_obj)

    #for obj in new_objects.values():
        #scene.objects.link(obj)
        
    # TODO import helpers
    
    # helper = bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0))

    if import_eye_points and 'EYE' in pof_handler.chunks:
        eye_chunk = pof_handler.chunks['EYE']
        for i, e in enumerate(eye_chunk.eye_offset):
            if fore_is_y:
                e = e[0], e[2], e[1]
            bpy.ops.object.empty_add(type='SINGLE_ARROW', location=e)
            eye = context.active_object
            vec = mathutils.Vector(eye_chunk.eye_normal[i])
            if fore_is_y:
                vec = vec.xzy
                znorm = mathutils.Vector((0,0,1))
            else:
                znorm = mathutils.Vector((0,1,0))
            quat = znorm.rotation_difference(vec)
            eye.rotation_mode = 'QUATERNION'
            eye.rotation_quaternion = quat
            eye.rotation_mode = 'XYZ'
            eye.name = 'eye'
            print(new_objects)
            if eye_chunk.sobj_num[i] in new_objects.keys():
                eye.parent = new_objects[eye_chunk.sobj_num[i]]

    if import_special_points and 'SPCL' in pof_handler.chunks:
        special_chunk = pof_handler.chunks['SPCL']
        for i, p in enumerate(special_chunk.points):
            if fore_is_y:
                p = p[0], p[2], p[1]
            bpy.ops.object.empty_add(type='SPHERE', location=p)
            point = context.active_object
            point.empty_draw_size = special_chunk.point_radius[i]
            point.name = special_chunk.point_names[i].decode('UTF-8')
            point['Properties'] = special_chunk.point_properties[i].decode('UTF-8')

    if import_paths and 'PATH' in pof_handler.chunks:
        path_chunk = pof_handler.chunks['PATH']
        for i, p in enumerate(path_chunk.path_names):
            for j, v in enumerate(path_chunk.vert_list[i]):
                if fore_is_y:
                    v = v[0], v[2], v[1]
                bpy.ops.object.empty_add(type='SPHERE', location=v)
                this_vert = context.active_object
                this_vert.name = '{}-{}'.format(p.decode('UTF-8'), j)
                this_vert.empty_draw_size = path_chunk.vert_rad[i][j]
                par = path_chunk.path_parents[i].decode('UTF-8')
                if not j:
                    par_vert = this_vert
                if not j and par in scene.objects:
                    this_vert.parent = scene.objects[par]
                elif j:
                    this_vert.parent = par_vert
                this_vert['Parent'] = par
                this_vert['Turret'] = path_chunk.turret_sobj_num[i][j]
            
    # Import custom properties
    
    if import_header_data:
        scene['POF version'] = pof_handler.pof_ver
        scene['Object flags'] = pof_handler.header.obj_flags
        scene['Mass'] = pof_handler.header.mass
        # center of mass should be helper empty
        p = pof_handler.header.mass_center
        if fore_is_y:
            p = p[0], p[2], p[1]
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=p)
        bpy.context.active_object.name = 'center-mass'
        # have to break up inertia tensor b/c blender props only accept lists of ints/floats
        scene['Inertia-0'] = list(pof_handler.header.inertia_tensor[0])
        scene['Inertia-1'] = list(pof_handler.header.inertia_tensor[1])
        scene['Inertia-2'] = list(pof_handler.header.inertia_tensor[2])
        scene['Cross sections'] = pof_handler.header.num_cross_sections
        scene['Cross section depths'] = pof_handler.header.cross_section_depth
        scene['Cross section radii'] = pof_handler.header.cross_section_radius
        scene['Misc. info'] = ' '.join(pof_handler.chunks['PINF'].lines)

    # done

    scene.update()
    new_time = time.time()
    print("\ttime to add objects {}".format(new_time - cur_time))

    return {'FINISHED'}