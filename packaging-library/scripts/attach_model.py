#!/usr/bin/env python3
"""Attach a new local model after checking its GLB; never replace an existing model."""
import argparse,json,shutil
from pathlib import Path
from check_project import glb_json,check

def attach(project,bundle):
    project,bundle=project.resolve(),bundle.resolve()
    additions=json.loads((bundle/'product-config.json').read_text())
    if len(additions)!=1:raise ValueError('One model per attachment')
    pid,config=next(iter(additions.items()))
    if pid not in {p['id'] for p in json.loads((project/'src/posters.json').read_text())}:raise ValueError('Model ID does not match a poster')
    target=project/'src/structure/collection-products.json';models=json.loads(target.read_text())
    if pid in models:raise ValueError('Model already exists; use a versioned project copy for revisions')
    filename=config['file']
    if Path(filename).name!=filename or not filename.endswith('.glb'):raise ValueError('Unsafe model filename')
    source=bundle/filename;data,_=glb_json(source);nodes={n.get('name') for n in data['nodes']}
    if any(p['node'] not in nodes for p in config['parts']):raise ValueError('Missing part node')
    dest=project/'public/assets/packaging'/filename
    if dest.exists():raise ValueError('Model destination already exists')
    old=target.read_bytes()
    try:
        shutil.copy2(source,dest);models[pid]=config;target.write_text(json.dumps(models,ensure_ascii=False,indent=2)+'\n')
        result=check(project)
    except Exception:
        target.write_bytes(old)
        if dest.exists():dest.unlink()
        raise
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project',type=Path);p.add_argument('model_bundle',type=Path);a=p.parse_args()
    print(json.dumps(attach(a.project,a.model_bundle),ensure_ascii=False,indent=2))
