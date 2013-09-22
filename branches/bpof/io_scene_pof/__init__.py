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
            default="*.pof",
            options={'HIDDEN'},
            )
    use_smooth_groups = BoolProperty(
            name="Import smooth groups",
            description="Try to make smoothgroups using EdgeSplit modifier.",
            default=False,
            )   # Probably not very good at it
    # Helpers:
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
##    import_special_debris = BoolProperty(
##            name="Import subsystem debris",
##            description="Import special object debris.",
##            default=True,
##            )   # If debris selected, will import these on the same layer
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
            default=False,
            )
    texture_path = StringProperty(
            name="Texture path",
            description="Path to search for textures in.",
            default="/../maps/",
            #subtype="FILE_PATH",
            )
    texture_format = EnumProperty(
            name="Texture format",
            items=(('.dds', "*.dds", "DirectDraw Surface"),
                   ('.png', "*.png", "Portable Network Graphics"),
                   ('.tga', "*.tga", "Targa"),
                   ('.jpg', "*.jpg", "Joint Photographic Experts Group")),
            default='.dds')
    pretty_materials = BoolProperty(
            name="Make materials",
            description="Make Blender materials from normal, shine, glow maps if possible.",
            default=False,
            )

    def execute(self, context):
        from . import import_pof

        keywords = self.as_keywords(ignore=("filter_glob",))
        return import_pof.load(self, context, **keywords)

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "use_smooth_groups")
        layout.prop(self, "import_header_data")
        layout.prop(self, "fore_is_y")

        box = layout.box()
        box.label(text="Helpers")
        box.prop(self, "import_eye_points")
        box.prop(self, "import_paths")
        box.prop(self, "import_gun_points")
        box.prop(self, "import_mis_points")
        box.prop(self, "import_tgun_points")
        box.prop(self, "import_tmis_points")
        box.prop(self, "import_thrusters")
        box.prop(self, "import_glow_points")
        box.prop(self, "import_special_points")

        box = layout.box()
        box.label(text="Models")
        box.prop(self, "import_only_main")
        if not self.import_only_main:
            box.prop(self, "import_detail_levels")
            box.prop(self, "import_detail_boxes")
            box.prop(self, "import_debris")
            box.prop(self, "import_turrets")
            box.prop(self, "import_specials")
        box.prop(self, "import_shields")

        box = layout.box()
        box.label(text="Textures")
        box.prop(self, "import_textures")
        if self.import_textures:
            box.prop(self, "texture_path")
        box.prop(self, "pretty_materials")


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