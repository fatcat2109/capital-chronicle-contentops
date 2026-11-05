"""Retain actual public image bytes and compare with each bound local chart."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root.parents[3]))
from live_contentops.media_manifest_authority_v1 import read_public_image_bytes, image_metadata_from_bytes, visual_similarity_to_local_file

rows = json.loads((root / 'platform-media-input.json').read_bytes())
folder = Path(r'A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-d\media_assets\platform_readback')
folder.mkdir(exist_ok=True)
result = []
for row in rows:
    raw = read_public_image_bytes(row['public_image_url'])
    metadata = image_metadata_from_bytes(raw)
    extension = {'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp'}[metadata['mime_type']]
    path = folder / (row['destination'] + '.' + extension)
    path.write_bytes(raw)
    result.append({**row, **metadata, 'path': str(path), 'bytes': len(raw),
        'platform_sha256': hashlib.sha256(raw).hexdigest(),
        'visual_similarity': visual_similarity_to_local_file(raw, row['source_path'])})
(root / 'platform-media-byte-check.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
