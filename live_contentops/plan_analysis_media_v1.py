"""Original two-leg geometry figure for a full plan account; no price history."""
from hashlib import sha256
import json
from pathlib import Path


def render(plan, candidate, folder, *, frozen_at):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    from matplotlib.ticker import FuncFormatter
    from .public_time_v1 import public_timestamp
    from .event_article_guard_v1 import PUBLIC_NOTICE, CONFLICTS_NOTICE
    pair=candidate['directional_entries']
    data={key:{field:pair[key].get(field) for field in ('entry_bounds','stop_level','target_level','structure')}
          for key in ('pullback','breakout')}
    binding={'plan_id':plan['plan_id'],'registration_hash':plan['registration_hash'],'legs':data,'frozen_at':frozen_at,
             'notices':[PUBLIC_NOTICE,CONFLICTS_NOTICE]}
    digest=sha256(json.dumps(binding,sort_keys=True).encode()).hexdigest()
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    path=folder/('plan-geometry-'+digest[:20]+'.png')
    fig,axes=plt.subplots(1,2,figsize=(14,8),dpi=150,facecolor='#f6f5ef')
    fig.subplots_adjust(left=.09,right=.95,top=.70,bottom=.22,wspace=.36)
    fig.text(.07,.92,'CAPITAL CHRONICLE',fontsize=14,color='#24625b',weight='bold')
    fig.text(.07,.855,plan['asset_id']+' · two conditional structures',fontsize=25,color='#172c35',weight='bold')
    fig.text(.07,.795,'Original plan levels · '+public_timestamp(frozen_at),fontsize=13,color='#5e686b')
    for ax,key in zip(axes,('pullback','breakout')):
        leg=data[key];b=leg['entry_bounds'];lo,hi=b['minimum'],b['maximum'];stop,target=leg['stop_level'],leg['target_level']
        ax.set_facecolor('#f6f5ef');ax.set_title(key.capitalize(),fontsize=17,loc='left',pad=20)
        values=[lo,hi,stop,target];span=max(values)-min(values)
        ax.set_ylim(min(values)-span*.22,max(values)+span*.22);ax.set_xlim(0,1)
        ax.axhspan(lo,hi,color='#66ada0',alpha=.55)
        ax.hlines([stop,target],0,.73,colors=['#aa414c','#977600'],linewidths=2)
        structure=leg.get('structure') or {}
        if structure.get('level') is not None:
            ax.hlines(structure['level'],0,.73,color='#71828b',linestyle=':',linewidth=1.5)
        ax.text(.76,target,'Model\nobjective',va='center',fontsize=12,color='#806300')
        ax.text(.76,stop,'Invalidation',va='center',fontsize=12,color='#aa414c')
        ax.text(.08,(lo+hi)/2,'Conditional zone',va='center',fontsize=12,color='#173f39',bbox={'facecolor':'#f6f5ef','alpha':.8,'edgecolor':'none','pad':4})
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v,pos: f'{v:,.5f}'.rstrip('0').rstrip('.') if abs(v)<10 else f'{v:,.2f}'.rstrip('0').rstrip('.')))
        ax.tick_params(axis='y',labelsize=11,length=0,pad=8);ax.set_xticks([])
        for spine in ('top','right','bottom'): ax.spines[spine].set_visible(False)
        ax.spines['left'].set_color('#abb4b5')
        label=f"Zone {lo:g}–{hi:g}  |  Invalidation {stop:g}  |  Objective {target:g}"
        ax.text(0,-.14,label,transform=ax.transAxes,fontsize=10,color='#354950',wrap=True)
    fig.text(.07,.09,"Levels use the original plan's prices. This diagram shows conditions, not price history.",fontsize=12,color='#4e626a')
    fig.text(.07,.045,PUBLIC_NOTICE,fontsize=11,color='#4e626a')
    fig.text(.07,.02,CONFLICTS_NOTICE,fontsize=11,color='#4e626a')
    fig.savefig(path,facecolor=fig.get_facecolor());plt.close(fig)
    return {'asset_id':'analysis-geometry-'+digest[:20],'path':str(path.resolve()),'sha256':sha256(path.read_bytes()).hexdigest(),
            'width':2100,'height':1200,'mime_type':'image/png','modality':'plan_fact_card','media_role':'article',
            'article_inclusion':True,'canonical_article_media':True,'placement_after':'introduction',
            'rights_basis':"Capital Chronicle original diagram of its exact source-bound plan geometry (decision 113).",
            'attribution':'Capital Chronicle','caption':"The original pullback and breakout structures. Levels use the plan's prices; this is a level diagram, not price history.",
            'alt_text':plan['asset_id']+' original conditional pullback and breakout levels, invalidation and model objectives.',
            'chart_spec':binding,'provenance_status':'VERIFIED_CAPITAL_CHRONICLE_PLAN_EXPORT'}
