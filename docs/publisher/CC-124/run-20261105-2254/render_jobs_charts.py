"""Render MAX-selected jobs charts from the exact admitted source packet."""
from pathlib import Path
from hashlib import sha256
import json
import re
import sys

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_editorial_data_chart, validate_editorial_data_chart

OP = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-nfp-us500-preview-20261105-g")
response = OP / 'desktop_response_visual-edit.json'
assert sha256(response.read_bytes()).hexdigest() == '0847c28ce552bc62fafd0677d0ef6583fedb85a1ac16e53dfbb09f029722ca02'
decision = json.loads(response.read_bytes())['output']
recovered = json.loads((OP / 'editorial_media_plan_required.json').read_bytes())
docs = recovered['source_pack']
assert len(docs) == 6
for d in docs:
    assert sha256(d['canonical_content_text'].encode()).hexdigest() == d['canonical_content_sha256']
bls = next(d for d in docs if d['document_id'] == 'cc124-bls-september-employment-original')
treasury = next(d for d in docs if d['document_id'] == 'cc124-treasury-nominal-20261104')

def operand(doc, token, excerpt, metric, unit, period):
    assert excerpt in doc['canonical_content_text'] and token in excerpt
    return dict(document_id=doc['document_id'], source_content_sha256=doc['canonical_content_sha256'],
        support_excerpt=excerpt, value_text=token, metric=metric, unit=unit,
        source_period_text='Sept. 2026' if doc is bls else period, prepared_period=period,
        period_basis={'kind':'EXACT_OFFICIAL_TABLE_OR_DATE_ROW', 'source_period':period})

table = bls['canonical_content_text'].split('Table B-1.')[1]
rows = {}
for label in ['Total nonfarm', 'Total private', 'Goods-producing', 'Private service-providing']:
    match = re.search(re.escape(label) + r'((?: [\d,]+){9})', table)
    assert match, label
    tokens = match[1].strip().split()
    rows[label] = (tokens, 'Table B-1.' + table[:match.end()])
    assert int(tokens[7].replace(',',''))-int(tokens[6].replace(',','')) == int(tokens[8])
nf, private = rows['Total nonfarm'][0], rows['Total private'][0]
government = int(nf[8])-int(private[8])
aug_government = int(nf[6].replace(',',''))-int(private[6].replace(',',''))
sep_government = int(nf[7].replace(',',''))-int(private[7].replace(',',''))
assert government == sep_government-aug_government == -17
points = []
for display, label in [('Private goods-producing','Goods-producing'), ('Private services','Private service-providing')]:
    tok, excerpt = rows[label]
    points.append(dict(period=display,value=int(tok[8]),transform='IDENTITY',scale=1,observation_kind='REPORTED_ACTUAL',
        inputs=[operand(bls,tok[8],excerpt,label+' monthly change','thousands of jobs','September 2026')]))
points.append(dict(period='Government',value=government,transform='DIFFERENCE',scale=1,observation_kind='ESTIMATE',
    inputs=[operand(bls,rows[label][0][8],rows[label][1],label+' monthly change','thousands of jobs','September 2026') for label in ['Total nonfarm','Total private']]))
assert sum(p['value'] for p in points) == int(nf[8]) == 29
yield_points=[]
for match in re.finditer(r'^(2026-\d\d-\d\d) (\d+\.\d+)$',treasury['canonical_content_text'],re.M):
    date,value=match.groups()
    if '2026-09-01' <= date <= '2026-11-04':
        yield_points.append(dict(period=date,value=float(value),transform='IDENTITY',scale=1,observation_kind='REPORTED_ACTUAL',
            inputs=[operand(treasury,value,match[0],'Nominal 10-year Treasury par yield','Percent',date)]))
assert yield_points[0]['period']=='2026-09-01' and yield_points[-1]['period']=='2026-11-04' and yield_points[-1]['value']==4.90
assert len({p['period'] for p in yield_points}) == len(yield_points)
assets=[]
for choice in decision['charts']:
    spec=choice['data_spec']
    payroll=choice['asset_id']=='cc124-jobs-payroll-employer-groups'
    packet=dict(asset_id=choice['asset_id'],question=choice['question'],placement_after=choice['placement_after'],
        destination_subset=[d for d,ids in decision['channel_media'].items() if choice['asset_id'] in ids],
        title=spec['title'],subtitle=spec['subtitle'],unit='thousands of jobs' if payroll else 'Percent',
        chart_type='horizontal_diverging_bar' if payroll else 'line',
        series=[dict(series_id='EMPLOYER_GROUPS' if payroll else 'US10Y_PAR',name='September total nonfarm +29' if payroll else 'Nominal 10-year; final 4.90%',points=points if payroll else yield_points)],
        source_caption='Source: U.S. Bureau of Labor Statistics, 2 October 2026. Calculations/chart: Capital Chronicle.' if payroll else 'Source: U.S. Department of the Treasury. Independent chart: Capital Chronicle.',
        caption='September preliminary estimates: private goods +18, private services +28, government -17; total nonfarm +29 thousand jobs. Government is derived as total nonfarm minus total private.' if payroll else 'Exact official observations from 1 September through 4 November 2026; final nominal par yield 4.90%. Dated context, not live US10Y CFD pricing or causal evidence.',
        alt_text='September payroll changes, thousands of jobs: private goods-producing +18, private services +28, government -17. Sum: +29. Seasonally adjusted, preliminary.' if payroll else 'Official nominal 10-year Treasury daily par yields from 1 September to 4 November 2026, ending at 4.90 percent.',
        missingness=spec['missingness'],source_vintage_note=spec['vintage'],value_label_decimals=0 if payroll else 2)
    asset=build_editorial_data_chart(packet,docs,output_dir=OP/'media_assets/jobs-source-bound-r1')
    validate_editorial_data_chart(asset,docs)
    assets.append(asset)
out=OP/'media_assets'
source_path=out/'jobs-chart-source-documents.json'
source_path.write_text(json.dumps(docs,indent=2)+'\n',encoding='utf-8')
manifest=out/'jobs-chart-assets-unreviewed.json'
manifest.write_text(json.dumps(dict(operation_id=OP.name,visual_request_sha256='ed46a179bd885928885e678e71547977d97d09107da406e382d9474c128b73ef',media_assets=assets,pixel_review='PENDING_ACTUAL_IMAGE_INSPECTION',source_documents_path=str(source_path),source_documents_sha256=sha256(source_path.read_bytes()).hexdigest(),reconciliation=dict(goods=18,private_services=28,total_private=46,government=government,total_nonfarm=29,august_government=aug_government,september_government=sep_government,treasury_observation_count=len(yield_points),treasury_last=4.90)),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(manifest_path=str(manifest),manifest_sha256=sha256(manifest.read_bytes()).hexdigest(),assets=[{k:a[k] for k in ['asset_id','path','sha256','width','height']} for a in assets])))
