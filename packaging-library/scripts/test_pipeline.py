import json,sys,tempfile,unittest
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent))
from new_project import create
from check_project import check,glb_json
from attach_model import attach

class PipelineTests(unittest.TestCase):
    def test_import_preserves_originals_deduplicates_and_checks_resources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'in';source.mkdir()
            Image.new('RGB',(120,200),'#eedddd').save(source/'产品.png')
            (source/'重复.png').write_bytes((source/'产品.png').read_bytes())
            result=create(source,root/'out','clear','测试库')
            self.assertEqual(result['uniquePosters'],1)
            report=check(root/'out');self.assertEqual(report['posters'],1);self.assertEqual(report['models'],[])
            p=json.loads((root/'out/src/posters.json').read_text())[0]
            self.assertEqual((root/'out/public'/p['original'].lstrip('/')).read_bytes(),(source/'产品.png').read_bytes())
            with self.assertRaises(ValueError):create(source,root/'out','clear','重复')
            old=(root/'out/src/posters.json').read_text();p['original']='/../../outside.png'
            (root/'out/src/posters.json').write_text(json.dumps([p]))
            with self.assertRaises(ValueError):check(root/'out')
            (root/'out/src/posters.json').write_text(old)
            (root/'out/public'/p['image'].lstrip('/')).unlink()
            with self.assertRaises(ValueError):check(root/'out')
    def test_bad_image_leaves_no_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'in';source.mkdir();(source/'bad.png').write_bytes(b'not an image')
            with self.assertRaises(Exception):create(source,root/'out','natural','测试库')
            self.assertFalse((root/'out').exists())
    def test_glb_corruption_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'broken.glb';p.write_bytes(b'glTF'+b'0'*40)
            with self.assertRaises(ValueError):glb_json(p)
    def test_attachment_and_failed_revision_do_not_replace_existing_model(self):
        kit=Path(__file__).resolve().parents[1];starter=kit/'assets/starter'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'in';source.mkdir();Image.new('RGB',(50,50),'white').save(source/'sample.png')
            create(source,root/'out','natural','测试库');pid=json.loads((root/'out/src/posters.json').read_text())[0]['id']
            bundle=root/'bundle';bundle.mkdir();config=json.loads((starter/'src/structure/collection-products.json').read_text())['poster-072']
            (bundle/config['file']).write_bytes((starter/'public/assets/packaging'/config['file']).read_bytes())
            (bundle/'product-config.json').write_text(json.dumps({pid:config}))
            report=attach(root/'out',bundle);self.assertEqual(len(report['models']),1)
            old=(root/'out/src/structure/collection-products.json').read_bytes()
            with self.assertRaises(ValueError):attach(root/'out',bundle)
            self.assertEqual((root/'out/src/structure/collection-products.json').read_bytes(),old)
    def test_bad_node_leaves_project_unchanged(self):
        kit=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'in';source.mkdir();Image.new('RGB',(50,50),'white').save(source/'sample.png')
            create(source,root/'out','bold','测试库');pid=json.loads((root/'out/src/posters.json').read_text())[0]['id']
            bundle=root/'bundle';bundle.mkdir();(bundle/'sample.glb').write_bytes((kit/'assets/starter/public/assets/packaging/poster-072.glb').read_bytes())
            config={'file':'sample.glb','parts':[{'key':'missing','node':'MissingNode'}]};(bundle/'product-config.json').write_text(json.dumps({pid:config}))
            with self.assertRaises(ValueError):attach(root/'out',bundle)
            self.assertEqual(json.loads((root/'out/src/structure/collection-products.json').read_text()),{})
            self.assertFalse((root/'out/public/assets/packaging/sample.glb').exists())
if __name__=='__main__':unittest.main()
