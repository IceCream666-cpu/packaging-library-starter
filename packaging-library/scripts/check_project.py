#!/usr/bin/env python3
"""Check actual image paths and GLB node names, not just the existence of JSON."""
import argparse, hashlib, json, struct
from pathlib import Path

def glb_json(path):
    raw=path.read_bytes()
    if len(raw)<20:raise ValueError('Truncated GLB')
    magic,version,length=struct.unpack_from('<4sII',raw)
    if (magic,version,length)!=(b'glTF',2,len(raw)):raise ValueError('Invalid GLB header')
    size,kind=struct.unpack_from('<II',raw,12)
    if kind!=0x4E4F534A or 20+size>len(raw):raise ValueError('Invalid GLB JSON chunk')
    return json.loads(raw[20:20+size]),hashlib.sha256(raw).hexdigest()

def check(root):
    root=root.resolve();public=root/'public'
    def resource(route):
        target=(public/route.lstrip('/')).resolve()
        if public not in target.parents:raise ValueError('Resource escapes public directory')
        if not target.is_file():raise ValueError('Missing resource: '+route)
        return target
    def load(name):return json.loads((root/'src'/name).read_text())
    posters=load('posters.json');featured=load('featured.json');media=load('featured-media.json');models=load('structure/collection-products.json')
    ids=[x['id'] for x in posters]
    if not ids or len(set(ids))!=len(ids):raise ValueError('Poster IDs must be unique and nonempty')
    if len({x['id'] for x in featured})!=len(featured):raise ValueError('Duplicate featured IDs')
    if not {x['id'] for x in featured}<=set(ids):raise ValueError('Featured poster not found')
    for p in posters:
        for key in ('image','smallImage','thumb','stripThumb','original'):resource(p[key])
    for p in featured:
        for f in media[p['id']]['files'].values():resource('featured/'+Path(f['file']).name)
    report=[]
    for pid,model in models.items():
        if pid not in ids:raise ValueError('Model not associated with a poster')
        path=resource('assets/packaging/'+model['file']);data,digest=glb_json(path)
        nodes={n.get('name') for n in data.get('nodes',[])}
        parts=model['parts'];keys=[p['key'] for p in parts]
        if len(set(keys))!=len(keys):raise ValueError('Duplicate part key')
        for part in parts:
            if part['node'] not in nodes:raise ValueError('Missing GLB node: '+part['node'])
        if any('uri' in b for b in data.get('buffers',[])):raise ValueError('External GLB buffer')
        if any('uri' in t and not t['uri'].startswith('data:') for t in data.get('images',[])):raise ValueError('External model texture')
        explosion=model.get('review',{}).get('explosion')
        if explosion and not set(explosion['offsets'])<=set(keys):raise ValueError('Unknown explosion part')
        report.append({'id':pid,'bytes':path.stat().st_size,'sha256':digest,'parts':len(parts)})
    return {'status':'passed','posters':len(posters),'featured':len(featured),'models':report,'limit':'Structural check only; browser and visual fidelity still require review.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project',type=Path);a=p.parse_args()
    print(json.dumps(check(a.project),ensure_ascii=False,indent=2))
