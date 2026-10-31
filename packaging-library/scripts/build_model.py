"""Blender: --background --python-exit-code 1 --python build_model.py -- spec.json new-output-dir.
Data-only geometry recipe: no inferred dimensions, product identity or manufacturing claims.
"""
import json, math, re, sys
from pathlib import Path
import bpy
from mathutils import Vector

def build(spec_path,out):
    spec_path=spec_path.resolve();spec=json.loads(spec_path.read_text(encoding='utf-8'))
    if out.exists():raise ValueError('Output already exists; use a new revision directory')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,80}',spec['id']):raise ValueError('Invalid stable ID')
    if not spec['parts']:raise ValueError('At least one part is required')
    names=[p['node'] for p in spec['parts']];keys=[p['key'] for p in spec['parts']]
    if len(set(names))!=len(names) or len(set(keys))!=len(keys):raise ValueError('Duplicate node or key')
    # Bound inputs before mutating Blender's disposable background scene.
    for part in spec['parts']:
        for shape in part['shapes']:
            if shape['type'] not in ('lathe','box','label'):raise ValueError('Unsupported shape')
            if shape['type']=='lathe':
                profile=shape['profile']
                if len(profile)<2 or any(len(p)!=2 or not all(isinstance(x,(float,int)) and math.isfinite(x) for x in p) or p[1]<0 for p in profile):raise ValueError('Invalid lathe profile')
            if shape['type']=='label':
                texture=(spec_path.parent/shape['texture']).resolve()
                if not texture.is_relative_to(spec_path.parent) or not texture.is_file():raise ValueError('Missing local label texture')
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    groups=[];objects=[]
    for part in spec['parts']:
        group=bpy.data.objects.new(part['node'],None);bpy.context.collection.objects.link(group);groups.append(group)
        for idx,shape in enumerate(part['shapes']):
            name=f"{part['node']}_{idx}"
            if shape['type']=='lathe':
                n=64;verts=[];faces=[];depth=shape.get('depth',1);exponent=shape.get('exponent',2)
                if not .05<=depth<=10 or not 1<=exponent<=8:raise ValueError('Invalid section shape')
                for z,r in shape['profile']:
                    for i in range(n):
                        a=i*math.tau/n;c=math.cos(a);s=math.sin(a)
                        verts.append((r*math.copysign(abs(c)**(2/exponent),c),r*depth*math.copysign(abs(s)**(2/exponent),s),z))
                for j in range(len(shape['profile'])-1):
                    for i in range(n):
                        a=j*n+i;b=j*n+(i+1)%n;faces.append((a,b,b+n,a+n))
                if shape.get('capEnds',True):faces.extend([tuple(reversed(range(n))),tuple((len(shape['profile'])-1)*n+i for i in range(n))])
                mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
                for p in mesh.polygons:p.use_smooth=abs(p.normal.z)<.98
            elif shape['type']=='box':
                bpy.ops.mesh.primitive_cube_add(size=1);obj=bpy.context.object;obj.name=name;obj.scale=shape['size']
                bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
                if shape.get('bevel',0):
                    mod=obj.modifiers.new('Rounded edges','BEVEL');mod.width=shape['bevel'];mod.segments=4;bpy.ops.object.modifier_apply(modifier=mod.name)
            else:
                w,h=shape['size'];verts=[(-w/2,0,-h/2),(w/2,0,-h/2),(w/2,0,h/2),(-w/2,0,h/2)]
                mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],[(0,1,2,3)]);mesh.update();obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
                uv=mesh.uv_layers.new()
                for loop,coord in zip(mesh.polygons[0].loop_indices,[(0,0),(1,0),(1,1),(0,1)]):uv.data[loop].uv=coord
            obj.location=shape.get('location',[0,0,0]);obj.parent=group;objects.append(obj)
            mat=bpy.data.materials.new(name+' material');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF')
            color=shape.get('color','#eeeeea')
            if not re.fullmatch(r'#[0-9a-fA-F]{6}',color):raise ValueError('Invalid material color')
            rgb=[int(color[i:i+2],16)/255 for i in (1,3,5)]
            bs.inputs['Base Color'].default_value=(*[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb],1)
            for key,input_name,default in [('roughness','Roughness',.3),('metallic','Metallic',0),('transmission','Transmission Weight',0)]:
                value=shape.get(key,default)
                if not 0<=value<=1:raise ValueError('Material value out of range')
                bs.inputs[input_name].default_value=value
            bs.inputs['IOR'].default_value=1.46
            if shape['type']=='label':
                tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(spec_path.parent/shape['texture']));tx.image.pack()
                mat.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color']);mat.node_tree.links.new(tx.outputs['Alpha'],bs.inputs['Alpha']);mat.surface_render_method='DITHERED'
            obj.data.materials.append(mat)
    bpy.context.view_layer.update();vertices=[o.matrix_world@v.co for o in objects for v in o.data.vertices]
    bottom=min(v.z for v in vertices);height=max(v.z for v in vertices)-bottom
    if height<=0:raise ValueError('Empty model')
    factor=2.9/height
    for group in groups:group.scale=(factor,)*3;group.location.z=-bottom*factor
    bpy.context.view_layer.update()
    out.mkdir(parents=True);pid=spec['id'];filename=pid+'.glb'
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(out/filename),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_extras=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(pid+'.blend')))
    parts=[{k:v for k,v in p.items() if k!='shapes'} for p in spec['parts']]
    offsets={p['key']:p.pop('offset',[0,0,0]) for p in parts}
    config={'file':filename,'scale':1,'kind':'collection','parts':parts,'review':{'appearance':spec.get('appearance',{'glass':False,'frosted':False,'clearLabel':False}),'explosion':{'offsets':offsets,'camera':spec.get('camera',{'centerY':[1.45,2.25],'height':[4.3,6.8],'width':[4.3,7.8],'centerX':[0,-.3]})}}}
    (out/'product-config.json').write_text(json.dumps({pid:config},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'model-info.json').write_text(json.dumps({'id':pid,'status':'draft','sourceSpec':spec_path.name,'illustrativeDimensions':True,'containsFormula':False,'parts':names,'normalizedHeight':2.9,'limitations':spec.get('limitations',[]),'reference':spec.get('reference','not supplied')},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('MODEL_DRAFT_EXPORTED',pid)
if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:]
    if len(args)!=2:raise ValueError('Expected spec.json and a new output directory')
    build(Path(args[0]),Path(args[1]))
