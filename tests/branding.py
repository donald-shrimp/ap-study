"""Brand assets remain faithful to the Rikyū logo across PWA and in-app surfaces."""
import json, struct
from pathlib import Path
from xml.etree import ElementTree as ET

root=Path(__file__).resolve().parents[1]
navy='#142d4e'
ns='{http://www.w3.org/2000/svg}'
internal=ET.parse(root/'assets/icons/hitomon-logo.svg').getroot()
external=ET.parse(root/'assets/icons/hitomon-app-icon.svg').getroot()
assert len(internal.findall('.//'+ns+'path'))==5
assert len(external.findall('.//'+ns+'path'))==6
assert {n.get('fill') for n in internal.iter(ns+'path')}=={navy}
assert {n.get('fill') for n in external.iter(ns+'path')}=={navy,'#ffffff'}
assert not any(n.tag==ns+'rect' for n in internal.iter()),'In-app logo must be transparent'
manifest=json.loads((root/'manifest.webmanifest').read_text())
assert manifest['theme_color']==navy
for path,size in [('icon-192.png',192),('icon-512.png',512),('apple-touch-icon.png',180)]:
    data=(root/'assets/icons'/path).read_bytes()
    assert data[:8]==b'\x89PNG\r\n\x1a\n'
    assert struct.unpack('>II',data[16:24])==(size,size)
for page in ['index.html','ap/index.html','fp2/index.html']:
    html=(root/page).read_text()
    assert 'class="brand-logo"' in html
    assert 'assets/icons/hitomon-logo.svg' in html
    assert 'assets/icons/hitomon-app-icon.svg' in html
    assert 'apple-touch-icon.png' in html
assert 'assets/icons/hitomon-logo.svg' in (root/'sw.js').read_text()
print('Brand SVGs, icons, and references: OK')
