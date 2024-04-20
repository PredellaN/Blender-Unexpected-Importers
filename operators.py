import os
import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

from .constants import ASSETS_FILE

from .importer_classes import E57Reader

# Function to append an asset from a blend file
def append_asset(action, asset_name):
    filepath = f"{ASSETS_FILE}\\{action}\\{asset_name}"
    bpy.ops.wm.append(
        filepath=filepath,
        filename=asset_name,
        directory=f"{ASSETS_FILE}\\{action}"
    )

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
        append_asset("NodeTree", "Voxelize")
        append_asset("Material", "Projected")

        current_folder = os.path.dirname(self.filepath)
        e57_reader = E57Reader(self.filepath)
        e57_reader.read_scans()

        for scan in e57_reader.scans:
            # Create a new mesh object
            mesh = bpy.data.meshes.new(name="Scan Mesh")
            mesh_obj = bpy.data.objects.new(scan.scan_name, mesh)
            context.collection.objects.link(mesh_obj)
            context.view_layer.objects.active = mesh_obj

            # Add vertices to the mesh
            vertices = scan.points_local
            mesh.from_pydata(vertices, [], [])

            # Assign colors to vertices if available
            if scan.points_colors is not None:
                color_attr = mesh.attributes.new(name='Col', type='FLOAT_COLOR', domain='POINT')
                for i, vertex in enumerate(mesh.vertices):
                    c = scan.points_colors[i]
                    color_attr.data[i].color = [c[0]/255, c[1]/255, c[2]/255, 1]

            # Update mesh geometry
            mesh.update()

            mesh_obj.data.materials.append(bpy.data.materials['Projected'])
            mesh_obj.material_slots[0].material = mesh_obj.material_slots[0].material.copy()

            # Assign Projected material, copy it, and assign the environment image
            projected_material = mesh_obj.material_slots[0].material
            projected_material.name = f"Projected_{mesh_obj.name}"
            env_texture_node = next((node for node in projected_material.node_tree.nodes if node.type == 'TEX_ENVIRONMENT'), None)
            image_path = os.path.join(current_folder, f"{mesh_obj.name}.jpg")
            image = bpy.data.images.load(image_path, check_existing=True)
            env_texture_node.image = image

            # Add the Voxelize modifier to turn points into a visible mesh
            modifier = mesh_obj.modifiers.new(name="Voxelize Modifier", type='NODES')
            modifier.node_group = bpy.data.node_groups["Voxelize"]

            # Create an empty at the camera location
            empty = bpy.data.objects.new(scan.scan_name + "_Location", None)
            empty.location = scan.camera_location
            
            # Set the rotation of the empty using the quaternion
            empty.rotation_mode = 'QUATERNION'
            empty.rotation_quaternion = scan.camera_rotation

            # Link the empty to the scene and set it as the parent of the mesh object
            context.collection.objects.link(empty)
            mesh_obj.parent = empty

        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(ImportE57.bl_idname, text="E57 (.e57)")