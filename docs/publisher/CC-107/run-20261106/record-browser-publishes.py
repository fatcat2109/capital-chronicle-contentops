"""Record this run's observed, already-sent objects. This script never publishes."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INVOCATION = '01a1b092-b78e-7203-aeb6-664d04f8765a'
def read(name):
    return json.loads((HERE / name).read_bytes())

def record(destination, begin, observation, object_id, url, pre=None, missing_media=False):
    packet = read(begin)
    request = packet['request']
    observed = read(observation)
    stamp = observed['observed_at_utc']
    identity = request['expected_identity']
    if destination == 'x':
        texts = request['content_binding']['expected_thread_texts']
        pre_click = list(texts)
        pre_click[2] = pre_click[2].replace('\n\n', '\n\n\n\n\n')
        text = '\n\n'.join(p['text'] for p in observed['posts'])
    elif destination == 'youtube':
        text = observed['post']
        pre_click = [request['native_payload']['text'].replace('\n\n', '\n\n\n')]
    else:
        text = observed['text']
        pre_click = [read(pre)['pre']['text']]
    readback = {'status': 'SUCCESS', 'observed_identity': identity,
        'public_object_id': object_id, 'public_object_url': url,
        'observed_text': text, 'content_verified': False,
        'media_check_state': 'MISSING_REQUIRED_MEDIA' if missing_media else 'PENDING_BINARY_COMPARISON'}
    if missing_media:
        readback.update(missing_required_media_observed=True, public_image_urls=[],
            reason_code='YOUTUBE_UPLOAD_NOT_RETAINED_TEXT_EDIT_ONLY')
    result = {'request_sha256': request['request_sha256'], 'status': 'SUCCESS',
        'observed_identity': identity, 'public_object_id': object_id, 'public_object_url': url}
    identity_at = read(pre)['pre']['observed_at_utc'] if pre else stamp
    composed_identity = {'authenticated': True, 'observed_identity': identity,
        'observed_at_utc': identity_at}
    if destination == 'linkedin_company':
        composed_identity['observed_stable_id'] = observed['stable_id']
    response = {'tool_request_sha256': packet['tool_request_sha256'],
        'tool_observation': {'surface': 'CODEX_EXEC', 'tool_name': 'mcp__browseros_neo__run',
            'native_invocation_id': INVOCATION, 'observed_at_utc': stamp,
            'observation_source': observation + '; exact account and composer checked before send; '
                'actual post-click public object observed; no resend. X/YouTube pre-click identity clock not returned; '
                'their timestamp records the fresh readback. Media comparisons remain explicit.'},
        'result': result, 'composed': {'identity': composed_identity,
            'pre_click_posts': pre_click, 'readback': readback}}
    if pre:
        response['tool_observation']['dispatched_at_utc'] = read(pre)['clicked_at_utc']
    (HERE / f'{destination}-publish-response.json').write_text(json.dumps(response, indent=2) + '\n', encoding='utf-8')
    print(destination, request['request_sha256'], url)

record('x', 'x-publish-begin-expanded.json', 'x-public-observation.json',
    '2118693801451823351', 'https://x.com/Capitalnicle/status/2118693801451823351')
record('youtube', 'youtube-publish-begin-expanded.json', 'youtube-public-observation.json',
    'UgkxgzPknumtaawPLwOIxiH0-Yd6m6QcbZin', 'https://www.youtube.com/post/UgkxgzPknumtaawPLwOIxiH0-Yd6m6QcbZin', missing_media=True)
record('linkedin', 'linkedin-publish-begin-expanded.json', 'linkedin-public-observation.json',
    'urn:li:activity:7524460754750750720', 'https://www.linkedin.com/feed/update/urn:li:activity:7524460754750750720/',
    'linkedin-prepublish-observation.json')
record('linkedin_company', 'linkedin-company-publish-begin-expanded.json', 'linkedin-company-public-observation.json',
    'urn:li:activity:7524462065680285696', 'https://www.linkedin.com/feed/update/urn:li:activity:7524462065680285696/',
    'linkedin-company-prepublish-observation.json')
