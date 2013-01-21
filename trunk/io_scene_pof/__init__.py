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

# <pep8 compliant>

bl_info = {
    "name": "FS2_Open POF format",
    "author": "Christopher Koch",
    "blender": (2, 6, 5),
    "location": "File > Import-Export",
    "description": "Import-Export POF, Import POF mesh, textures, "
                   "and helper objects.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}

if "bpy" in locals():
    import imp
    if "import_obj" in locals():
        imp.reload(import_obj)
    if "export_obj" in locals():
        imp.reload(export_obj)


import bpy
from bpy.props import (BoolProperty,
                       FloatProperty,
                       StringProperty,
                       EnumProperty,
                       )
from bpy_extras.io_utils import (ExportHelper,
                                 ImportHelper,
                                 path_reference_mode,
                                 )

class ImportPOF(bpy.types.Operator, ImportHelper):
    """Load a FS2_Open POF File"""
    bl_idname = "import_scene.pof"
    bl_label = "Import POF"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".pof"
    filter_glob = StringProperty(
            default="*.pof;*.vp",
            options={'HIDDEN'},
            )

##    from_vp = BoolProperty(
##            name="Import from VP",
##            description="Import from a VP file - select a VP instead of a POF.",
##            default=False,
##            )
##    pof_name = StringProperty(
##            name="POF name",
##            description="Path to the file within the VP.",
##            )
    use_smooth_groups = BoolProperty(
            name="Import smooth groups",
            description="Try to make smoothgroups using EdgeSplit modifier.",
            default=False,
            )   # Probably not very good at it
    # Helpers:
    import_center_points = BoolProperty(
            name="Import center points",
            description="Import center points as empties.",
            default=False,
            )   # Centers are calculated automatically during export
    import_bound_boxes = BoolProperty(
            name="Import bounding boxes",
            description="Import bounding boxes.",
            default=False,
            )   # Bounding boxes are calculated automatically during export
    import_eye_points = BoolProperty(
            name="Import viewpoints",
            description="Import eye points as empties.",
            default=True,
            )   # Imported as vector empties
    import_paths = BoolProperty(
            name="Import paths",
            description="Import path points as empties.",
            default=True,
            )   # Imported as sphere empties parented to first point in path
    import_gun_points = BoolProperty(
            name="Import guns",
            description="Import gun points as empties.",
            default=True,
            )   # Imported as vector empties
    import_mis_points = BoolProperty(
            name="Import missiles",
            description="Import missile points as empties.",
            default=True,
            )   # Imported as vector empties
    import_tgun_points = BoolProperty(
            name="Import gun turrets",
            description="Import turret gun points as empties.",
            default=True,
            )   # Imported as vector empties
    import_tmis_points = BoolProperty(
            name="Import missile turrets",
            description="Import turret missile points as empties.",
            default=True,
            )   # Imported as vector empties
    import_thrusters = BoolProperty(
            name="Import thrusters",
            description="Import thrusters as empties.",
            default=True,
            )   # Imported as sphere empties
    import_glow_points = BoolProperty(
            name="Import glows",
            description="Import glow points as empties.",
            default=True,
            )   # Imported as sphere empties
##    import_flash_points = BoolProperty(
##            name="Import muzzleflashes",
##            description="Import muzzleflash lights as empties.",
##            default=True,
##            )   # Imported as regular empties
    import_special_points = BoolProperty(
            name="Import special points",
            description="Import special points as empties.",
            default=True,
            )   # Imported as sphere empties
    import_header_data = BoolProperty(
            name="Import header",
            description="Import extra header data as scene custom properties.",
            default=True,
            )
    # Models:
    import_only_main = BoolProperty(
            name="Import only hull",
            description="Import only main LOD and its children.",
            default=False,
            )
    import_detail_levels = BoolProperty(
            name="Import all LODs",
            description="Import LOD models.",
            default=True,
            )   # Will import each LOD on a separate layer
    import_detail_boxes = BoolProperty(
            name="Import detail boxes",
            description="Import detail box models.",
            default=True,
            )
    import_debris = BoolProperty(
            name="Import debris",
            description="Import debris models.",
            default=True,
            )   # Will import on a separate layer from LODs.
    import_turrets = BoolProperty(
            name="Import turrets",
            description="Import turret models.",
            default=True,
            )   # If LODs selected, will import these parented appropriately
    import_specials = BoolProperty(
            name="Import subsystems",
            description="Import special objects (subsystems).",
            default=True,
            )
    import_special_debris = BoolProperty(
            name="Import subsystem debris",
            description="Import special object debris.",
            default=True,
            )   # If debris selected, will import these on the same layer
    fore_is_y = BoolProperty(
            name="Switch axes",
            description="If true, fore is Blender's +Y-axis.",
            default=True,
            )   # Otherwise, fore is Z-axis
    import_shields = BoolProperty(
            name="Import shield",
            description="Import wireframe shield mesh.",
            default=True,
            )   # Imports on same layer as highest detail level
    # Textures:
    import_textures = BoolProperty(
            name="Import textures",
            description="Import textures and UV data.",
            default=True,
            )
    texture_path = StringProperty(
            name="Texture path",
            description="Path to search for textures in.",
            default="../maps/",
            subtype="FILE_PATH",
            )
    make_materials = BoolProperty(
            name="Make materials",
            description="Make Blender materials from normal, shine, glow maps if possible.",
            default=False,
            )

    def execute(self, context):
##        # print("Selected: " + context.active_object.name)
##        from . import import_obj
##
##        if self.split_mode == 'OFF':
##            self.use_split_objects = False
##            self.use_split_groups = False
##        else:
##            self.use_groups_as_vgroups = False
##
##        keywords = self.as_keywords(ignore=("axis_forward",
##                                            "axis_up",
##                                            "filter_glob",
##                                            "split_mode",
##                                            ))
##
##        global_matrix = axis_conversion(from_forward=self.axis_forward,
##                                        from_up=self.axis_up,
##                                        ).to_4x4()
##        keywords["global_matrix"] = global_matrix
##
##        return import_obj.load(self, context, **keywords)

        from . import import_pof

        keywords = self.as_keywords(ignore=("filter_glob",))
        return import_pof.load(self, context, **keywords)

##    def draw(self, context):
##        layout = self.layout

##        row = layout.row(align=True)
##        row.prop(self, "use_ngons")
##        row.prop(self, "use_edges")
##
##        layout.prop(self, "use_smooth_groups")
##
##        box = layout.box()
##        row = box.row()
##        row.prop(self, "split_mode", expand=True)
##
##        row = box.row()
##        if self.split_mode == 'ON':
##            row.label(text="Split by:")
##            row.prop(self, "use_split_objects")
##            row.prop(self, "use_split_groups")
##        else:
##            row.prop(self, "use_groups_as_vgroups")
##
##        row = layout.split(percentage=0.67)
##        row.prop(self, "global_clamp_size")
##        layout.prop(self, "axis_forward")
##        layout.prop(self, "axis_up")
##
##        layout.prop(self, "use_image_search")


def menu_func_import(self, context):
    self.layout.operator(ImportPOF.bl_idname, text="Parallax Object File (.pof)")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_func_import)
    #bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_func_import)
   # bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()