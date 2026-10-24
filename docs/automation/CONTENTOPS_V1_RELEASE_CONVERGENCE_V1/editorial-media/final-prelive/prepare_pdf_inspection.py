"""Rasterize actual Neo-rendered PDFs and make bounded visual inspection sheets."""
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'renders/final'
POP=Path('C:/Users/bullw/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')
observations=json.loads((OUT/'browser-observations.json').read_bytes())
for item in observations:
    slug,width=item['slug'],item['viewport']
    pdf=OUT/(slug+'-'+width+'.pdf')
    reader=PdfReader(pdf);item['pdf']={'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
        'pages':len(reader.pages),'bytes':pdf.stat().st_size,'retained_path':str(pdf),
        'text_characters':sum(len(p.extract_text() or '') for p in reader.pages)}
    raster=OUT/(slug+'-'+width+'-page')
    result=subprocess.run([str(POP),'-r','96','-png',str(pdf),str(raster)],capture_output=True,text=True)
    if result.returncode:raise RuntimeError(result.stderr)
    pages=sorted(OUT.glob(raster.name+'-*.png'))
    for start in range(0,len(pages),4):
        group=pages[start:start+4];thumbs=[]
        for p in group:
            im=Image.open(p).convert('RGB')
            if width=='desktop':
                # Preserve the whole actual1060px reader column on1440px pages.
                im=im.crop((max(0,int(im.width*0.13)),0,min(im.width,int(im.width*.87)),im.height))
                im.thumbnail((680,1240))
            else:im.thumbnail((390,1800))
            thumbs.append(im)
        cols=2 if width=='desktop' else 4
        cellw=max(i.width for i in thumbs);cellh=max(i.height for i in thumbs)+32
        sheet=Image.new('RGB',(cols*cellw,((len(thumbs)+cols-1)//cols)*cellh),'#cbd1ca');draw=ImageDraw.Draw(sheet)
        for j,im in enumerate(thumbs):
            x=(j%cols)*cellw;y=(j//cols)*cellh
            draw.text((x+8,y+7),f'{slug} {width} page {start+j+1}',fill='#172f35')
            sheet.paste(im,(x,y+30))
        sheet.save(OUT/f'{slug}-{width}-inspection-{start//4+1}.jpg',quality=88)
(OUT/'browser-observations.json').write_text(json.dumps(observations,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'pdfs':len(observations),'pages':sum(x['pdf']['pages'] for x in observations),'inspection_sheets':[p.name for p in sorted(OUT.glob('*inspection*.jpg'))]}))
