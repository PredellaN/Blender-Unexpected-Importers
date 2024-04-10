import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

from .importer_classes import E57Reader

class ImportE57(Operator, ImportHelper):
    bl_idname = "import.e57"
    bl_label = "Import E57"

    filename_ext = ".e57"

    filter_glob: StringProperty(
        default="*" + filename_ext,
        options={'HIDDEN'},
        maxlen=255,
    ) # type: ignore

    def execute(self, context):
        e57_reader = E57Reader(self.filepath)
        e57_reader.read_scans()

        for scan_data in e57_reader.scans:
            # Create a new mesh object
            mesh = bpy.data.meshes.new(name="Scan Mesh")
            mesh_obj = bpy.data.objects.new("Scan Object", mesh)
            context.collection.objects.link(mesh_obj)
            context.view_layer.objects.active = mesh_obj

            # Add vertices to the mesh
            vertices = scan_data['points_global']
            mesh.from_pydata(vertices, [], [])

            # Update mesh geometry
            mesh.update()

        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(ImportE57.bl_idname, text="E57 (.e57)")