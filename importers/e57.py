import os
import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator

import pye57
import numpy as np

class Scan:
    def __init__(self, scan_index, e57_file):
        self.scan_index = scan_index
        self.e57_file = e57_file
        self.scan_name = None
        self.points_local = None
        self.camera_location = None
        self.camera_rotation = None
        self.points_global = None
        self.points_colors = None

    def process_scan(self):
        data = self.e57_file.read_scan_raw(self.scan_index)
        header = self.e57_file.get_header(self.scan_index)

        self.scan_name = header.node['name'].value()
        self.points_local = np.column_stack([
            data['cartesianX'],
            data['cartesianY'],
            data['cartesianZ'],
        ])

        self.camera_location = header.translation
        self.camera_rotation = header.rotation
        self.points_global = self.e57_file.to_global(
            self.points_local, header.rotation, header.translation)

        if 'colorRed' in data:
            self.points_colors = np.column_stack([
                data['colorRed'],
                data['colorGreen'],
                data['colorBlue'],
            ]).astype(np.uint8)

class E57Reader:
    def __init__(self, filepath):
        self.filepath = filepath
        self.scans = []
        self.has_colors = False

    def read_scans(self):
        with pye57.E57(self.filepath, 'r') as e57:
            num_scans = e57.scan_count
            for scan_index in range(num_scans):
                scan = Scan(scan_index, e57)
                scan.process_scan()
                self.scans.append(scan)
                if scan.points_colors is not None:
                    self.has_colors = True

class Import(Operator, ImportHelper):
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

        for scan in e57_reader.scans:
            verts = np.asarray(scan.points_local, dtype=np.float32)   # (N,3) float32
            n_verts = verts.shape[0]

            mesh = bpy.data.meshes.new(name=scan.scan_name + "_mesh")
            mesh_obj = bpy.data.objects.new(scan.scan_name, mesh)
            context.collection.objects.link(mesh_obj)
            context.view_layer.objects.active = mesh_obj

            mesh.vertices.add(n_verts)
            mesh.vertices.foreach_set("co", verts.ravel())

            if scan.points_colors is not None:
                cols = np.asarray(scan.points_colors, dtype=np.float32) / 255.0  # (N,3) 0–1
                color_attr = mesh.color_attributes.new(
                    name="Col", type='FLOAT_COLOR', domain='POINT'
                )
                cols4 = np.empty((n_verts, 4), dtype=np.float32)
                cols4[:, :3] = cols
                cols4[:, 3] = 1.0
                color_attr.data.foreach_set("color", cols4.ravel())

            mesh.update()

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
    self.layout.operator(Import.bl_idname, text="E57 (.e57)")