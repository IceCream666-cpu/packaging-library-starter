#!/usr/bin/env python3
"""Create a separate poster library; preserve every input and refuse overwrites."""
import argparse, hashlib, json, shutil, tempfile
from pathlib import Path
from html import escape
from PIL import Image, ImageOps

PALETTES={'natural':('#eee6da','#353b30',['#c4b392','#69745c']), 'clear':('#e6eef0','#223b43',['#94bec2','#e3ebe8']), 'bold':('#f5d4df','#462238',['#ea7c9d','#ecc751'])}
EXTS={'.png','.jpg','.jpeg','.webp'}

def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def create(source, dest, style, name):
    source,dest=source.resolve(),dest.resolve()
    if not source.is_dir(): raise ValueError('海报目录不存在')
    if dest.exists(): raise ValueError('目标已存在；请选择新的项目目录，以免覆盖旧作品')
    if source == dest or source in dest.parents: raise ValueError('输出目录请放在海报目录之外')
    files=sorted(p for p in source.iterdir() if p.is_file() and p.suffix.lower() in EXTS)
    if not files: raise ValueError('没有可用海报；支持 PNG/JPG/JPEG/WebP')
    # Decode all images before creating any deliverable.
    for path in files:
        with Image.open(path) as im: im.verify()
    dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.packaging-',dir=dest.parent) as tmp:
        out=Path(tmp)/'project'
        shutil.copytree(Path(__file__).resolve().parents[1]/'assets/starter',out,ignore=shutil.ignore_patterns('node_modules','dist'))
        for p in (out/'public/assets').iterdir():
            if p.is_file() and p.name != 'library-mark.svg':p.unlink()
        for p in (out/'public/featured').iterdir():p.unlink()
        for p in (out/'public/assets/packaging').glob('*.glb'):p.unlink()
        bg,ink,swatch=PALETTES[style];posters=[];featured=[];media={};records=[]
        for index,path in enumerate(files,1):
            raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest();pid='item-'+digest[:16]
            if any(p['id']==pid for p in posters):continue
            original=out/'public/assets'/f'{pid}-original{path.suffix.lower()}';original.write_bytes(raw)
            with Image.open(path) as im:
                image=ImageOps.exif_transpose(im).convert('RGBA');width,height=image.size
                def derivative(folder,filename,size):
                    copy=image.copy();copy.thumbnail((size,size),Image.Resampling.LANCZOS)
                    destfile=out/'public'/folder/filename;destfile.parent.mkdir(parents=True,exist_ok=True);copy.save(destfile,'WEBP',quality=88)
                    return copy.size
                iw,ih=derivative('assets',pid+'.webp',1280);sw,sh=derivative('assets',pid+'-small.webp',512)
                tw,th=derivative('assets',pid+'-thumb.webp',192)
                variants={}
                for size in (640,1024):
                    fn=f'{pid}-{size}.webp';fw,fh=derivative('featured',fn,size)
                    variants[str(size)]={'file':'featured/'+fn,'width':fw,'height':fh}
            title=path.stem
            posters.append({'id':pid,'title':{'zh':title,'en':title},'category':'all','style':style,'image':'/assets/'+pid+'.webp','imageWidth':iw,'imageHeight':ih,'smallImage':'/assets/'+pid+'-small.webp','smallWidth':sw,'smallHeight':sh,'thumb':'/assets/'+pid+'-thumb.webp','stripThumb':'/assets/'+pid+'-thumb.webp','stripWidth':tw,'stripHeight':th,'original':'/assets/'+original.name,'width':width,'height':height})
            featured.append({'id':pid,'name':title,'kind':{'zh':'产品海报','en':'Product poster'},'description':{'zh':'点击查看原海报。','en':'Open the original poster.'},'background':bg,'ink':ink,'swatch':swatch})
            media[pid]={'width':width,'height':height,'files':variants}
            records.append({'id':pid,'sourceFile':path.name,'sourceSha256':digest,'state':'poster_ready','modelStatus':'not_started','unknown':['title_requires_review','category_requires_review','geometry','material','dimensions','back_view'],'notes':'首页暂用完整海报；产品抠图和3D由 AI 按原图另行制作。'})
        for fn,data in [('posters.json',posters),('featured.json',featured),('featured-media.json',media),('poster-palettes.json',{}),('asset-paths.json',{}),('structure/collection-products.json',{})]:write(out/'src'/fn,data)
        index=out/'index.html';index.write_text(index.read_text().replace('包材库 · 可复用示例',escape(name)+' · 包材库'),encoding='utf-8')
        write(out/'src/brand.json',{'name':name,'nameEn':name,'tagline':'产品与包材展示','taglineEn':'Products and packaging','hero':name})
        write(out/'intake.json',{'schemaVersion':1,'style':style,'products':records})
        # Atomic hand-off after validation. No files are replaced at the destination.
        out.rename(dest)
    return {'project':str(dest),'uniquePosters':len(posters),'models':0,'style':style}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--posters',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--style',choices=PALETTES,default='natural');p.add_argument('--name',default='我的包材库')
    a=p.parse_args();print(json.dumps(create(a.posters,a.out,a.style,a.name),ensure_ascii=False,indent=2))
