import os
import sys
import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator

import numpy as np

class Import(Operator, ImportHelper):
    bl_idname = "import.ifc"
    bl_label = "Import ifc"

    filename_ext = ".ifc"

    filter_glob: StringProperty(
        default="*" + filename_ext,
        options={'HIDDEN'},
        maxlen=255,
    ) # type: ignore

    def execute(self, context):
        parser = IFCParser()
        parser.parse(self.filepath)
        parser.summary()
        load_to_blender(parser)

        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(Import.bl_idname, text="IFC (.ifc)")


###

class IFCEntity:
    def __init__(self, id_, type_, params):
        self.id = id_
        self.type = type_
        self.params = params  # raw params, numpy arrays, or parsed lists

    def __repr__(self):
        return f"<IFC#{self.id} {self.type} {self.params}>"

class IFCParser:
    import re
    ENTITY_RE = re.compile(r'^#(\d+)\s*=\s*([A-Za-z0-9_]+)\s*\((.*)\);$')

    def __init__(self):
        self.entities = {}  # id (int) -> IFCEntity

    def parse(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        in_data = False
        buffer = ''
        for ln in lines:
            ln = ln.strip()
            if ln.upper() == 'DATA;':
                in_data = True
                continue
            if not in_data:
                continue
            if ln.upper() == 'ENDSEC;':
                break
            buffer += ln
            if buffer.endswith(';'):
                self._parse_line(buffer)
                buffer = ''

    def _parse_line(self, line):
        m = self.ENTITY_RE.match(line)
        if not m:
            return
        eid_str, type_name, params_str = m.groups()
        eid = int(eid_str)
        params = self._split_params(params_str)
        t = type_name.upper()
        # handle numeric arrays
        if t in ('IFCCARTESIANPOINT', 'IFCDIRECTION'):
            coords = self._parse_number_list(params[0])
            arr = np.array(coords, dtype=float)
            ent = IFCEntity(eid, t, arr)
        # handle reference lists
        elif t == 'IFCPOLYLOOP':
            refs = self._parse_ref_list(params[0])
            ent = IFCEntity(eid, t, refs)
        elif t == 'IFCFACE':
            bounds = self._parse_ref_list(params[0])
            ent = IFCEntity(eid, t, bounds)
        else:
            ent = IFCEntity(eid, t, params)
        self.entities[eid] = ent

    def _split_params(self, s):
        params = []
        buf = ''
        depth = 0
        for c in s:
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
            if c == ',' and depth == 0:
                params.append(buf.strip())
                buf = ''
            else:
                buf += c
        if buf:
            params.append(buf.strip())
        return params

    def _parse_number_list(self, s):
        s = s.strip()
        if s.startswith('(') and s.endswith(')'):
            s = s[1:-1]
        nums = []
        for part in s.split(','):
            p = part.strip()
            try:
                if '.' in p or 'E' in p.upper():
                    nums.append(float(p))
                else:
                    nums.append(int(p))
            except ValueError:
                nums.append(p)
        return nums

    def _parse_ref_list(self, s):
        s = s.strip()
        if s.startswith('(') and s.endswith(')'):
            s = s[1:-1]
        refs = []
        for part in s.split(','):
            p = part.strip()
            if p.startswith('#'):
                refs.append(int(p[1:]))
        return refs

    def summary(self):
        types = {}
        for e in self.entities.values():
            types.setdefault(e.type, 0)
            types[e.type] += 1
        print('Parsed entities by type:')
        for t, count in sorted(types.items()):
            print(f'  {t}: {count}')
        print(f'Total: {len(self.entities)} entities')


def load_to_blender(parser, obj_name='IFCMesh'):
    # Collect vertices
    pts = [e.params for e in parser.entities.values() if e.type=='IFCCARTESIANPOINT']
    ids = [e.id for e in parser.entities.values() if e.type=='IFCCARTESIANPOINT']
    id_to_idx = {eid:i for i,eid in enumerate(ids)}
    verts = np.vstack(pts)

    # Collect faces
    faces = []
    for ent in parser.entities.values():
        if ent.type == 'IFCFACE':
            for bound_id in ent.params:
                bound = parser.entities.get(bound_id)
                if not bound: continue
                # bound.params[0] is loop ref id, as string or int
                loop_id = bound.params[0] if isinstance(bound.params[0], int) else int(bound.params[0].lstrip('#'))
                loop = parser.entities.get(loop_id)
                if not loop: continue
                verts_idx = [id_to_idx[r] for r in loop.params]
                faces.append(verts_idx)

    # Create Blender mesh
    mesh = bpy.data.meshes.new(obj_name)
    obj = bpy.data.objects.new(obj_name, mesh)
    bpy.context.collection.objects.link(obj)

    mesh.vertices.add(len(verts))
    mesh.loops.add(sum(len(f) for f in faces))
    mesh.polygons.add(len(faces))

    # assign coords
    mesh.vertices.foreach_set('co', verts.flatten())

    # build loops
    loop_verts = []
    for f in faces:
        loop_verts.extend(f)
    mesh.loops.foreach_set('vertex_index', loop_verts)

    # build polygon data
    loop_start = []
    loop_total = []
    idx = 0
    for f in faces:
        loop_start.append(idx)
        loop_total.append(len(f))
        idx += len(f)
    mesh.polygons.foreach_set('loop_start', loop_start)
    mesh.polygons.foreach_set('loop_total', loop_total)

    mesh.validate()
    mesh.update()
    print(f"Created Blender mesh '{obj_name}' with {len(verts)} verts, {len(faces)} faces.")