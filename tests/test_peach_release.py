"""Portable Peach integrity, not automated visual or aesthetic acceptance."""
import hashlib,json,struct,unittest,zlib
from pathlib import Path
from base_constraints import check_skin
ROOT=Path(__file__).resolve().parents[1]
PEACH=ROOT/'styles/peachlight-cloud-valley'
class PeachReleaseTests(unittest.TestCase):
    def test_manifest_covers_complete_package(self):
        m=json.loads((PEACH/'manifest.json').read_text())
        self.assertEqual({x['path'] for x in m['files']},{str(p.relative_to(PEACH)) for p in PEACH.rglob('*') if p.is_file() and p.name!='manifest.json'})
        for x in m['files']:
            b=(PEACH/x['path']).read_bytes()
            with self.subTest(path=x['path']):
                self.assertEqual(len(b),x['bytes']); self.assertEqual(hashlib.sha256(b).hexdigest(),x['sha256'])
    def test_seven_images_and_prompts(self):
        self.assertEqual(len(list(PEACH.rglob('*.png'))),7); self.assertEqual(len(list(PEACH.rglob('*.txt'))),7)
        self.assertEqual(len(list((PEACH/'baseline').glob('*.png'))),1); self.assertEqual(len(list((PEACH/'examples').glob('*.png'))),6)
    def test_png_integrity_and_actual_dimensions(self):
        for p in PEACH.rglob('*.png'):
            with self.subTest(path=p.name):
                b=p.read_bytes(); self.assertEqual(b[:8],b'\x89PNG\r\n\x1a\n'); pos=8; kinds=[]; compressed=bytearray()
                while pos<len(b):
                    n=struct.unpack('>I',b[pos:pos+4])[0]; kind=b[pos+4:pos+8]; payload=b[pos+8:pos+8+n]
                    self.assertEqual(zlib.crc32(kind+payload)&0xffffffff,struct.unpack('>I',b[pos+8+n:pos+12+n])[0]); kinds.append(kind)
                    if kind==b'IHDR': w,h,d,c,co,f,i=struct.unpack('>IIBBBBB',payload)
                    if kind==b'IDAT': compressed.extend(payload)
                    pos+=n+12
                self.assertEqual((w,h),(1672,941)); self.assertEqual((d,co,f,i),(8,0,0,0)); self.assertIn(c,(2,6))
                self.assertEqual((kinds[0],kinds[-1]),(b'IHDR',b'IEND')); self.assertEqual(pos,len(b))
                pixels=zlib.decompress(compressed); stride=w*(3 if c==2 else 4)+1
                self.assertEqual(len(pixels),stride*h); self.assertTrue(all(pixels[row*stride]<=4 for row in range(h)))
    def test_actual_prompts_posthoc_skin_check(self):
        for p in PEACH.rglob('*.txt'):
            with self.subTest(path=p.name): self.assertTrue(check_skin(p.read_text(),{'rendering_medium':'photoreal','visible_humans':True})['exact_sentence_present'])
    def test_honest_provenance_and_acceptance(self):
        m=json.loads((PEACH/'manifest.json').read_text())
        self.assertIn('manual',m['execution']); self.assertIn('not compiler outputs',m['execution']); self.assertEqual((m['baseline_count'],m['new_testcase_count']),(1,6))
        self.assertFalse(m['competitor_images_included']); self.assertIn('not individually approved',m['new_testcase_status']); self.assertIn('No compiler was used',(PEACH/'QA.md').read_text())
    def test_preserved_base_and_absent_root_readme(self):
        self.assertEqual(hashlib.sha256((ROOT/'base-image-production/base.json').read_bytes()).hexdigest(),'dd349aca7c6075f57cd7d358d811e69aae308795bf958f9c7af4a694ccbadd9a')
        self.assertEqual(hashlib.sha256((ROOT/'compose_prompt.py').read_bytes()).hexdigest(),'afcc26444355590616c1fbcab70f299f7a58b9cd5d17eee9f37595aa2e6792c8')
        self.assertFalse((ROOT/'README.md').exists()); self.assertFalse((ROOT/'preflight.py').exists())
