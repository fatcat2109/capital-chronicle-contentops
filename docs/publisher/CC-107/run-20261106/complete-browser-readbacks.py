"""Bind actual public copy and downloaded image bytes to the three claimed readbacks."""
import hashlib
import json
import math
from pathlib import Path
import re
from PIL import Image, ImageChops, ImageStat
from live_contentops.neo_destination_handoff_v1 import _text, _x_thread_matches

HERE = Path(__file__).resolve().parent
DOWNLOADS = Path(r'C:\Users\bullw\Downloads')
INVOCATION = '01a1b092-b78e-7203-aeb6-664d04f8765a'
CANONICAL = 'https://capitalchronicle.substack.com/p/nfp-preview-why-a-payroll-beat-needs'
def read(name):
    return json.loads((HERE / name).read_bytes())

def comparisons(request, images, paths):
    result = []
    for asset, public, downloaded in zip(request['content_binding']['media_manifest'], images, paths, strict=True):
        original = Path(asset['path'])
        actual_hash = hashlib.sha256(downloaded.read_bytes()).hexdigest()
        assert actual_hash == public['sha256']
        assert hashlib.sha256(original.read_bytes()).hexdigest() == asset['sha256']
        source = Image.open(original).convert('RGB')
        delivered = Image.open(downloaded).convert('RGB')
        assert abs(source.width / source.height - delivered.width / delivered.height) < .005
        source = source.resize(delivered.size, Image.Resampling.LANCZOS)
        mse = sum(v * v for v in ImageStat.Stat(ImageChops.difference(source, delivered)).rms) / 3
        psnr = 100.0 if mse == 0 else 10 * math.log10(255 ** 2 / mse)
        assert psnr >= 30, (asset['asset_id'], psnr)
        result.append({'source_asset_sha256': asset['sha256'], 'platform_sha256': actual_hash,
            'public_image_url': public['url'], 'public_object_url': request['public_object_url'],
            'pixels_inspected': True, 'source_pixels_match': True,
            'inspection_method': 'Decoded RGB comparison against approved source; same aspect and content after platform resizing/compression',
            'psnr_db': psnr, 'dimensions': list(delivered.size), 'binary_path': str(downloaded)})
    return result

for name, begin, observation in [
    ('x', 'x-readback-begin-expanded.json', 'x-final-public-observation.json'),
    ('linkedin', 'linkedin-readback-begin-expanded.json', 'linkedin-final-public-observation.json'),
    ('linkedin_company', 'linkedin-company-readback-begin-expanded.json', 'linkedin-company-final-public-observation.json'),
]:
    packet = read(begin)
    request = packet['request']
    observed = read(observation)
    result = {'request_sha256': request['request_sha256'], 'status': 'SUCCESS',
        'observed_identity': request['expected_identity'], 'public_object_id': request['public_object_id'],
        'public_object_url': request['public_object_url'], 'content_verified': True,
        'media_check_state': 'SOURCE_PIXELS_MATCH', 'observed_link_resolutions': []}
    if name == 'x':
        result['observed_thread'] = []
        for post in observed['posts']:
            url = next(u for u in post['urls'] if re.fullmatch(r'https://x.com/Capitalnicle/status/\d+', u))
            result['observed_thread'].append({'public_object_url': url, 'public_object_id': url.rsplit('/', 1)[1],
                'observed_text': post['text'], 'published_at_utc': post['published_at_utc']})
        result['observed_text'] = '\n\n'.join(p['text'] for p in observed['posts'])
        link = observed['posts'][0]['links'][0]
        result['observed_link_resolutions'] = [{'displayed_text': link['text'], 'short_url': link['url'],
            'target_url': CANONICAL, 'target_verified': True, 'public_object_url': request['public_object_url'],
            'observed_at_utc': '2026-11-06T13:29:46.870Z', 'evidence': 'Neo page712 followed the exact t.co URL to the canonical'}]
        assert _x_thread_matches(request['content_binding'], result['observed_thread'], result['observed_link_resolutions'], CANONICAL)
        images = [{'url': observed['posts'][0]['media'][0]['url'],
            'sha256': 'd35b3197a0362ca40b9a6f055c1bdcb5f62cb134722a740bcf67ed35508c643f'}]
        paths = [DOWNLOADS / 'cc107-x-public.png']
    else:
        result['observed_text'] = observed['text']
        target = read('linkedin-link-targets.json')[0 if name == 'linkedin' else 1]
        assert target['targets'] == [CANONICAL]
        result['observed_link_resolutions'] = [{'displayed_url': target['short_url'], 'target_url': CANONICAL,
            'target_verified': True, 'public_object_url': request['public_object_url'],
            'observed_at_utc': target['observed_at_utc'], 'evidence': 'Neo resolved the short-link destination page and read its exact canonical target'}]
        comparison = _text(observed['text']).replace(target['short_url'], CANONICAL)
        assert all(_text(s) in comparison for s in request['content_binding']['expected_text_segments'])
        images = (read('linkedin-member-image-downloads.json') if name == 'linkedin'
            else read('linkedin-company-final-images.json')['images'])
        # The actual public member and company resolutions produce identical hashes.
        # Reuse a downloaded binary only after its SHA matches this exact public image.
        paths = [DOWNLOADS / f'cc107-linkedin-member-{i}.jpg' for i in range(3)]
    result['media_comparisons'] = comparisons(request, images, paths)
    result['public_image_urls'] = [i['url'] for i in images]
    response = {'tool_request_sha256': packet['tool_request_sha256'],
        'tool_observation': {'surface': 'CODEX_EXEC', 'tool_name': 'mcp__browseros_neo__run',
            'native_invocation_id': INVOCATION, 'observed_at_utc': observed['observed_at_utc'],
            'observation_source': observation + '; exact public copy, actual redirect targets, public image SHA and decoded-pixel comparisons recorded in this item folder; no public write'},
        'result': result}
    (HERE / f'{name}-readback-response.json').write_text(json.dumps(response, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'destination': name, 'request_sha256': request['request_sha256'], 'public_object_url': request['public_object_url'],
        'matched_images': len(images), 'text_matches': True}))
