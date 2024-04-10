import bpy

class UDPropertyGroup(bpy.types.PropertyGroup):
    scale: bpy.props.IntProperty(
        name='Scale',
        soft_max=1000,
        default=50,
        min=0,
    ) # type: ignore