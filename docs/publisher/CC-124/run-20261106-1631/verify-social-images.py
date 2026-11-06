"""Compare exact public platform images with the approved article card."""
import json
import subprocess
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parents[3]))
from live_contentops.media_manifest_authority_v1 import image_metadata_from_bytes, visual_similarity_to_local_file

LOCAL = BASE / 'media/media_assets/post-facts-fc5c1c6572545a5197e3.png'
OUTPUT = BASE / 'media/readback'
OUTPUT.mkdir(exist_ok=True)
results = []
for name in ['x', 'youtube', 'linkedin', 'linkedin_company']:
    obs = json.loads((BASE / (name + '-readback-observation.json')).read_bytes())
    images = obs.get('images') or obs['posts'][0]['images']
    url = images[0]['url']
    target = OUTPUT / (name + '.bin')
    # Binary-only transport: no browser/session headers and no image bytes in stdout.
    subprocess.run(['curl.exe', '--fail', '--silent', '--show-error', '--location',
                    '--max-time', '18', '--output', str(target), url], check=True)
    raw = target.read_bytes()
    metadata = image_metadata_from_bytes(raw)
    extension = metadata['mime_type'].split('/')[-1].replace('jpeg', 'jpg')
    binary = OUTPUT / (name + '.' + extension)
    target.rename(binary)
    result = {'destination': name, 'public_object_url': obs['url'], 'public_image_url': url,
        'binary_path': str(binary), 'platform_sha256': sha256(raw).hexdigest(),
        'source_asset_sha256': sha256(LOCAL.read_bytes()).hexdigest(), 'bytes': len(raw),
        **metadata, 'visual_similarity': visual_similarity_to_local_file(raw, LOCAL),
        'dimension_ratio_matches': abs(metadata['width']/metadata['height'] - 1080/1350) < .005,
        'pixels_inspected': False, 'source_pixels_match': False}
    results.append(result)
    print(json.dumps(result), flush=True)
packet = {'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'comparisons': results,
          'inspection_state': 'BINARY_COMPARISON_COMPLETE_PIXEL_INSPECTION_PENDING'}
(BASE / 'social-image-comparisons.json').write_text(json.dumps(packet, indent=2)+'\n', encoding='utf-8')
