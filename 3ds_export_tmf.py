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

bl_info = {
    "name": "Export 3DS for TrackMania Forever",
    "author": "Glauco Bacchi, Campbell Barton, Bob Holcomb, Richard Lärkäng, Damien McGinnes, Mark Stijnman",
    "version": (1, 0, 0),
    "blender": (2, 7, 9),
    "location": "File > Export > 3DS for TMF (.3ds)",
    "description": "Export 3DS model for TrackMania Forever (.3ds)",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export"
}

import bpy
import bpy_extras
import time

###### EXPORT OPERATOR #######
class Export_tmf(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    """Export 3DS model for Trackmania Forever"""
    bl_idname = "export_scene.tmf"
    bl_label = "Export 3DS for TMF (.3ds)"

    filename_ext = ".3ds"

    def execute(self, context):
        start_time = time.time()
        print('\n_____START_____')
        props = self.properties
        filepath = self.filepath
        filepath = bpy.path.ensure_ext(filepath, self.filename_ext)

        exported = do_export(filepath)

        if exported:
            print('finished export in %s seconds' %((time.time() - start_time)))
            print(filepath)

        return {'FINISHED'}


### REGISTER ###

def menu_func(self, context):
    self.layout.operator(Export_tmf.bl_idname, text="3DS for TMF (.3ds)")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_export.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()

def do_export(filename):
    return True
