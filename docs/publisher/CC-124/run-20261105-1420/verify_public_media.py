"""Verify exact observed Substack originals with the existing media authority."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from live_contentops.media_manifest_authority_v1 import original_substack_media_url, read_public_image_bytes

root = Path(__file__).resolve().parent
obs = json.loads((root / 'substack-public-dom-observation.json').read_bytes())
media = json.loads((root / 'substack-media-manifest.json').read_bytes())
ordered = [media[4], *media[:4]]
assert len(obs['images']) == len(ordered) == 5
checks = []
for image, asset in zip(obs['images'], ordered):
    url = original_substack_media_url(image['src'])
    raw = read_public_image_bytes(url)
    digest = hashlib.sha256(raw).hexdigest()
    check = {'asset_id': asset['asset_id'], 'original_url': url, 'bytes': len(raw),
             'sha256': digest, 'expected_sha256': asset['sha256'],
             'matches_exact_bound_asset': digest == asset['sha256'],
             'alt_matches': image['alt'] == asset['alt_text']}
    checks.append(check)
    assert check['matches_exact_bound_asset'] and check['alt_matches'], check
(root / 'public-media-hash-check.json').write_text(json.dumps(checks, indent=2), encoding='utf-8')
print(json.dumps(checks))
