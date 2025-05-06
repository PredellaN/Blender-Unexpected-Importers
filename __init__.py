import bpy, os

### Constants
ADDON_FOLDER = os.path.dirname(os.path.abspath(__file__))
PG_NAME = "UnexpectedImporters"
TYPES_NAME = "unexpectedimporters"
PACKAGE: str = __package__ or "unexpectedimporters"


### Blender Addon Initialization
bl_info = {
    "name" : "Blender Unexpected Importers",
    "author" : "Nicolas Predella",
    "description" : "",
    "blender" : (4, 1, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

### Initialization
from .importers import e57, ifc

modules = [
    e57.Import,
    ifc.Import
]

def register():

    for module in modules:
        bpy.utils.register_class(module)
    
    bpy.types.TOPBAR_MT_file_import.append(e57.menu_func_import)
    # bpy.types.TOPBAR_MT_file_import.append(ifc.menu_func_import)

def unregister():   
    for module in modules:
        bpy.utils.unregister_class(module)

    bpy.types.TOPBAR_MT_file_import.remove(e57.menu_func_import)
    # bpy.types.TOPBAR_MT_file_import.append(ifc.menu_func_import)

if __name__ == "__main__":
    register()