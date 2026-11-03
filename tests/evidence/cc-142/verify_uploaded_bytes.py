"""Read only the four exact public asset files uploaded for the reviewed CPI edit."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parent
uploaded = json.loads((root / 'uploaded-editor-images.json').read_bytes())['nodes']
assets = json.loads((root / 'reviewed-assets.json').read_bytes())
if isinstance(assets, dict):
    assets = assets['assets']
rows = []
for node, asset in zip(uploaded, assets, strict=True):
    url = node['content'][0]['attrs']['src']
    if not url.startswith('https://substack-post-media.s3.amazonaws.com/public/images/'):
        raise ValueError('EXACT_PUBLIC_UPLOAD_HOST_REQUIRED')
    with urlopen(Request(url, headers={'User-Agent': 'CapitalChronicle/CC142-public-asset-readback'}), timeout=30) as response:
        content = response.read()
        actual = hashlib.sha256(content).hexdigest()
        rows.append({'asset_id': asset['asset_id'], 'url': url, 'status': response.status,
                     'bytes': len(content), 'expected_sha256': asset['sha256'],
                     'observed_sha256': actual, 'exact_bytes': actual == asset['sha256']})
if not all(row['exact_bytes'] for row in rows):
    raise ValueError(json.dumps(rows))
(root / 'uploaded-byte-readback.json').write_text(json.dumps({
    'observed_at_utc': datetime.now(timezone.utc).isoformat(),
    'action': 'READ_ONLY_EXACT_PUBLIC_UPLOADED_MEDIA', 'rows': rows,
}, indent=2)+'\n', encoding='utf-8')
print({'assets': len(rows), 'all_exact_bytes': True})
