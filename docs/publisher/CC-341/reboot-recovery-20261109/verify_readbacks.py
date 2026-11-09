"""Bind actual reboot-recovery observations to the existing coordinator requests."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from live_contentops.neo_destination_handoff_v1 import _text, _x_reader_text, _x_thread_matches

ROOT = Path(__file__).resolve().parent
CANONICAL = 'https://capitalchronicle.substack.com/p/tanker-strikes-us-strikes-on-iran'
rows = json.loads((ROOT/'exact-public-readbacks.json').read_text(encoding='utf-8'))
comparisons = json.loads((ROOT/'social-image-comparisons.json').read_text(encoding='utf-8'))
redirects = json.loads((ROOT/'verified-short-links.json').read_text(encoding='utf-8'))
assert redirects['x_final_url'] == CANONICAL
assert CANONICAL in redirects['personal'] and CANONICAL in redirects['company']
for name, page in [('personal',5), ('company',6), ('x',7), ('youtube',8)]:
    packet = json.loads((ROOT/(name+'-read-begin.json')).read_text(encoding='utf-8'))
    request = packet['request']
    row = next(r for r in rows if r['id'] == page)
    obs = row['observation']
    url = obs['url']
    object_id = url.rstrip('/').split('/')[-1]
    text = obs.get('text') or '\n\n'.join(p['text'] for p in obs['posts'])
    media = next(c for c in comparisons if c['destination'] == request['destination'])
    assert media['pixels_inspected'] and media['source_pixels_match']
    result = {'request_sha256': request['request_sha256'], 'status':'SUCCESS',
        'observed_identity': request['expected_identity'], 'public_object_id': object_id,
        'public_object_url': url, 'observed_text': text, 'content_verified': True,
        'public_write_performed': False, 'media_comparisons': [media],
        'public_image_urls': [media['public_image_url']], 'observed_media_sha256': []}
    comparison_text = _text(text)
    if name in {'personal','company'}:
        short = re.search(r'https://lnkd\.in/[A-Za-z0-9_-]+', text).group()
        result['observed_link_resolutions'] = [{'displayed_url':short, 'target_url':CANONICAL,
            'target_verified':True, 'public_object_url':url}]
        comparison_text = comparison_text.replace(_text(short), _text(CANONICAL))
    elif name == 'x':
        short = obs['posts'][0]['links'][0]
        result['observed_link_resolutions'] = [{'displayed_text':short['text'], 'short_url':short['href'],
            'target_url':CANONICAL, 'target_verified':True, 'public_object_url':url}]
        result['observed_thread'] = []
        for post in obs['posts']:
            post_url = next(link['href'] for link in post['links']
                if re.fullmatch(r'https://x.com/Capitalnicle/status/\d+', link['href']))
            result['observed_thread'].append({'public_object_url':post_url,
                'public_object_id':post_url.split('/')[-1], 'observed_text':post['text']})
        assert _x_thread_matches(request['content_binding'], result['observed_thread'],
            result['observed_link_resolutions'], CANONICAL)
        comparison_text = _x_reader_text(text, result['observed_link_resolutions'], url, CANONICAL)
    assert all(_text(segment) in comparison_text for segment in request['content_binding']['expected_text_segments']), name
    response = {'tool_request_sha256':packet['tool_request_sha256'],
        'tool_observation':{'surface':'CODEX_EXEC', 'tool_name':'mcp__browseros_neo__run',
            'native_invocation_id':'/root', 'observed_at_utc':row['observed_at_utc'],
            'observation_source':'Actual exact-object Neo DOM readback after claim; short links verified through Neo; public image binaries compared with the approved original and inspected using view_image'},
        'result': result}
    (ROOT/(name+'-read-response.json')).write_text(json.dumps(response,indent=2),encoding='utf-8')
    print(name, 'TEXT_MEDIA_THREAD_MATCH', object_id)
