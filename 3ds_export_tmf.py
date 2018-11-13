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
import struct

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

        bpy.context.window.cursor_set('WAIT')
        exported = do_export(filepath)
        bpy.context.window.cursor_set('DEFAULT')

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

######################################################
# Data Structures
######################################################

#Some of the chunks that we will export
#----- Primary Chunk, at the beginning of each file
PRIMARY                 = 0x4D4D

#------ Main Chunks
OBJECTINFO              = 0x3D3D  # This gives the version of the mesh and is found right before the material and object information
VERSION                 = 0x0002  # This gives the version of the .3ds file
KFDATA                  = 0xB000  # This is the header for all of the key frame info

#------ sub defines of OBJECTINFO
MATERIAL                = 45055  # 0xAFFF // This stored the texture info
OBJECT                  = 16384  # 0x4000 // This stores the faces, vertices, etc...

#>------ sub defines of MATERIAL
MATNAME                 = 0xA000  # This holds the material name
MATAMBIENT              = 0xA010  # Ambient color of the object/material
MATDIFFUSE              = 0xA020  # This holds the color of the object/material
MATSPECULAR             = 0xA030  # SPecular color of the object/material
MATSHINESS              = 0xA040  # Shininess of the object/material (percent)
MATSHIN2                = 0xA041  # Specularity of the object/material (percent)

MAT_DIFFUSEMAP          = 0xA200  # This is a header for a new diffuse texture
MAT_OPACMAP             = 0xA210  # head for opacity map
MAT_BUMPMAP             = 0xA230  # read for normal map
MAT_SPECMAP             = 0xA204  # read for specularity map

#>------ sub defines of MAT_???MAP
MATMAPFILE              = 0xA300  # This holds the file name of a texture
MAT_MAP_TILING          = 0xA351  # 2nd bit (from LSB) is mirror UV flag
MAT_MAP_USCALE          = 0xA354  # U axis scaling
MAT_MAP_VSCALE          = 0xA356  # V axis scaling
MAT_MAP_UOFFSET         = 0xA358  # U axis offset
MAT_MAP_VOFFSET         = 0xA35A  # V axis offset
MAT_MAP_ANG             = 0xA35C  # UV rotation around the z-axis in rad

MATTRANS                = 0xA050  # Transparency value (i.e. =100-OpacityValue) (percent)
PCT                     = 0x0030
MASTERSCALE             = 0x0100

RGB1                    = 0x0011
RGB2                    = 0x0012

#>------ sub defines of OBJECT
OBJECT_MESH             = 0x4100  # This lets us know that we are reading a new object
OBJECT_LIGHT            = 0x4600  # This lets un know we are reading a light object
OBJECT_CAMERA           = 0x4700  # This lets un know we are reading a camera object

#>------ sub defines of CAMERA
OBJECT_CAM_RANGES       = 0x4720  # The camera range values

#>------ sub defines of OBJECT_MESH
OBJECT_VERTICES         = 0x4110  # The objects vertices
OBJECT_FACES            = 0x4120  # The objects faces
OBJECT_MATERIAL         = 0x4130  # This is found if the object has a material, either texture map or color
OBJECT_UV               = 0x4140  # The UV texture coordinates
OBJECT_TRANS_MATRIX     = 0x4160  # The Object Matrix

#>------ sub defines of KFDATA
KFDATA_KFHDR            = 0xB00A
KFDATA_KFSEG            = 0xB008
KFDATA_KFCURTIME        = 0xB009
KFDATA_OBJECT_NODE_TAG  = 0xB002

#>------ sub defines of OBJECT_NODE_TAG
OBJECT_NODE_ID          = 0xB030
OBJECT_NODE_HDR         = 0xB010
OBJECT_PIVOT            = 0xB013
OBJECT_INSTANCE_NAME    = 0xB011
POS_TRACK_TAG           = 0xB020
ROT_TRACK_TAG           = 0xB021
SCL_TRACK_TAG           = 0xB022

BOUNDBOX                = 0xB014

# So 3ds max can open files, limit names to 12 in length
# this is very annoying for filenames!
name_unique = []  # stores str, ascii only
name_mapping = {}  # stores {orig: byte} mapping


def sane_name(name):
    name_fixed = name_mapping.get(name)
    if name_fixed is not None:
        return name_fixed

    # strip non ascii chars
    new_name_clean = new_name = name.encode("ASCII", "replace").decode("ASCII")[:12]
    i = 0

    while new_name in name_unique:
        new_name = new_name_clean + ".%.3d" % i
        i += 1

    # note, appending the 'str' version.
    name_unique.append(new_name)
    name_mapping[name] = new_name = new_name.encode("ASCII", "replace")
    return new_name


# size defines:
SZ_SHORT    = 2
SZ_INT      = 4
SZ_FLOAT    = 4

class _3ds_ushort(object):
    """Class representing a short (2-byte integer) for a 3ds file.
    *** This looks like an unsigned short H is unsigned from the struct docs - Cam***"""
    __slots__ = ("value", )

    def __init__(self, val=0):
        self.value = val

    def get_size(self):
        return SZ_SHORT

    def write(self, file):
        file.write(struct.pack("<H", self.value))

    def __str__(self):
        return str(self.value)

class _3ds_uint(object):
    """Class representing an int (4-byte integer) for a 3ds file."""
    __slots__ = ("value", )

    def __init__(self, val):
        self.value = val

    def get_size(self):
        return SZ_INT

    def write(self, file):
        file.write(struct.pack("<I", self.value))

    def __str__(self):
        return str(self.value)

class _3ds_float(object):
    """Class representing a 4-byte IEEE floating point number for a 3ds file."""
    __slots__ = ("value", )

    def __init__(self, val):
        self.value = val

    def get_size(self):
        return SZ_FLOAT

    def write(self, file):
        file.write(struct.pack("<f", self.value))

    def __str__(self):
        return str(self.value)

class _3ds_string(object):
    """Class representing a zero-terminated string for a 3ds file."""
    __slots__ = ("value", )

    def __init__(self, val=""):
        print(val)
        assert(type(val) == str)
        self.value = val

    def get_size(self):
        return (len(self.value) + 1)

    def write(self, file):
        binary_format = "<%ds" % (len(self.value) + 1)
        file.write(struct.pack(binary_format, self.value.encode('utf-8')))

    def __str__(self):
        return self.value

class _3ds_named_variable(object):
    """Convenience class for named variables."""

    __slots__ = "value", "name"

    def __init__(self, name, val=None):
        self.name = name
        self.value = val

    def get_size(self):
        if self.value is None:
            return 0
        else:
            return self.value.get_size()

    def write(self, file):
        if self.value is not None:
            self.value.write(file)

    def dump(self, indent):
        if self.value is not None:
            print(indent * " ",
                  self.name if self.name else "[unnamed]",
                  " = ",
                  self.value)

#the chunk class
class _3ds_chunk(object):
    """Class representing a chunk in a 3ds file.

    Chunks contain zero or more variables, followed by zero or more subchunks.
    """
    __slots__ = "ID", "size", "variables", "subchunks"

    def __init__(self, chunk_id=0):
        self.ID = _3ds_ushort(chunk_id)
        self.size = _3ds_uint(0)
        self.variables = []
        self.subchunks = []

    def add_variable(self, name, var):
        """Add a named variable.

        The name is mostly for debugging purposes."""
        self.variables.append(_3ds_named_variable(name, var))

    def add_subchunk(self, chunk):
        """Add a subchunk."""
        self.subchunks.append(chunk)

    def get_size(self):
        """Calculate the size of the chunk and return it.

        The sizes of the variables and subchunks are used to determine this chunk\'s size."""
        tmpsize = self.ID.get_size() + self.size.get_size()
        for variable in self.variables:
            tmpsize += variable.get_size()
        for subchunk in self.subchunks:
            tmpsize += subchunk.get_size()
        self.size.value = tmpsize
        return self.size.value

    def validate(self):
        for var in self.variables:
            func = getattr(var.value, "validate", None)
            if (func is not None) and not func():
                return False

        for chunk in self.subchunks:
            func = getattr(chunk, "validate", None)
            if (func is not None) and not func():
                return False

        return True

    def write(self, file):
        """Write the chunk to a file.

        Uses the write function of the variables and the subchunks to do the actual work."""
        #write header
        self.ID.write(file)
        self.size.write(file)
        for variable in self.variables:
            variable.write(file)
        for subchunk in self.subchunks:
            subchunk.write(file)

    def dump(self, indent=0):
        """Write the chunk to a file.

        Dump is used for debugging purposes, to dump the contents of a chunk to the standard output.
        Uses the dump function of the named variables and the subchunks to do the actual work."""
        print(indent * " ",
              "ID=%r" % hex(self.ID.value),
              "size=%r" % self.get_size())
        for variable in self.variables:
            variable.dump(indent + 1)
        for subchunk in self.subchunks:
            subchunk.dump(indent + 1)

######################################################
# EXPORT
######################################################

# COMMENTED OUT FOR 2.42 RELEASE!! CRASHES 3DS MAX
def make_kfdata(start=0, stop=0, curtime=0, rev=0):
    """Make the basic keyframe data chunk"""
    kfdata = _3ds_chunk(KFDATA)

    kfhdr = _3ds_chunk(KFDATA_KFHDR)
    kfhdr.add_variable("revision", _3ds_ushort(rev))
    # Not really sure what filename is used for, but it seems it is usually used
    # to identify the program that generated the .3ds:
    # 4KEX: Based on observations some sample 3DS files typically used start stop of 100 with curtime = 0
    kfhdr.add_variable("filename", _3ds_string("Blender"))
    kfhdr.add_variable("animlen", _3ds_uint(stop - start))

    kfseg = _3ds_chunk(KFDATA_KFSEG)
    kfseg.add_variable("start", _3ds_uint(start))
    kfseg.add_variable("stop", _3ds_uint(stop))

    kfcurtime = _3ds_chunk(KFDATA_KFCURTIME)
    kfcurtime.add_variable("curtime", _3ds_uint(curtime))

    kfdata.add_subchunk(kfhdr)
    kfdata.add_subchunk(kfseg)
    kfdata.add_subchunk(kfcurtime)
    return kfdata

def do_export(filename,use_selection=True):

    """Save the Blender scene to a 3ds file."""

    sce = bpy.context.scene

    # Initialize the main chunk (primary):
    primary = _3ds_chunk(PRIMARY)
    # Add version chunk:
    version_chunk = _3ds_chunk(VERSION)
    version_chunk.add_variable("version", _3ds_uint(3))
    primary.add_subchunk(version_chunk)

    # init main object info chunk:
    object_info = _3ds_chunk(OBJECTINFO)

    # COMMENTED OUT FOR 2.42 RELEASE!! CRASHES 3DS MAX
    # 4KEX: Enabled kfdata with changes. Hopefully will not crash 3DS MAX (not tested)
    # init main key frame data chunk:
    kfdata = make_kfdata(0, 100, 0, 1)

    # Make a list of all materials used in the selected meshes (use a dictionary,
    # each material is added once):
    materialDict = {}
    mesh_objects = []

    if use_selection:
        objects = (ob for ob in sce.objects if ob.is_visible(sce) and ob.select)
    else:
        objects = (ob for ob in sce.objects if ob.is_visible(sce))

    empty_objects = [ ob for ob in objects if ob.type == 'EMPTY' ]

    for ob in objects:
    # get derived objects
        free, derived = create_derived_objects(scene, ob)

        if derived is None:
            continue

        for ob_derived, mat in derived:
            if ob.type not in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}:
                continue

            try:
                data = ob_derived.to_mesh(scene, True, 'RENDER')
            except:
                data = None

            if data:
                # 4KEX: Removed mesh transformation. Will do this later based on parenting and other factors.
                # so vertices are in local coordinates
                # orig was the next line commented out
                data.transform(mat)
                # data.normal_update()
                mesh_objects.append((ob_derived, data))
                mat_ls = data.materials
                mat_ls_len = len(mat_ls)
                # get material/image tuples.
                if data.faceUV:
                    if not mat_ls:
                        mat = mat_name = None

                    for f in data.faces:
                        if mat_ls:
                            mat_index = f.mat
                            if mat_index >= mat_ls_len:
                                mat_index = f.mat = 0
                            mat = mat_ls[mat_index]
                            if mat: mat_name = mat.name
                            else:   mat_name = None
                        # else there alredy set to none

                        img = f.image
                        if img: img_name = img.name
                        else:   img_name = None

                        materialDict.setdefault((mat_name, img_name), (mat, img))

                else:
                    for mat in mat_ls:
                        if mat: # material may be None so check its not.
                            materialDict.setdefault((mat.name, None), (mat, None) )

                    # Why 0 Why!
                    for f in data.faces:
                        if f.mat >= mat_ls_len:
                            f.mat = 0

    # Make material chunks for all materials used in the meshes:
    for mat_and_image in materialDict.values():
        object_info.add_subchunk(make_material_chunk(mat_and_image[0], mat_and_image[1]))

    # 4KEX: Added MASTERSCALE element
    mscale = _3ds_chunk(MASTERSCALE)
    mscale.add_variable("scale", _3ds_float(1))
    object_info.add_subchunk(mscale)

    #
    #
    #
    #
    #

    # Create chunks for all empties:
    # 4KEX: Re-enabled kfdata. Empty objects not tested yet.
    for ob in empty_objects:
        # Empties only require a kf object node:
        kfdata.add_subchunk(make_kf_obj_node(ob, name_to_id, name_to_scale, name_to_pos, name_to_rot))

    # Add main object info chunk to primary chunk:
    primary.add_subchunk(object_info)

    # 4KEX: Export kfdata
    primary.add_subchunk(kfdata)

    # At this point, the chunk hierarchy is completely built.

    # Check the size:
    primary.get_size()
    # Open the file for writing:
    file = open(filename, 'wb')

    # Recursively write the chunks to file:
    primary.write(file)

    # Close the file:
    file.close()

    # Clear name mapping vars, could make locals too
    del name_unique[:]
    name_mapping.clear()

    return True

if __name__ == "__main__":
    register()
    do_export("/tmp/tmf_export.3ds")
