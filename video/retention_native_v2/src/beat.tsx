import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import type {BeatRenderJob, EditState} from './types';

const navy = '#07141f';
const ink = '#f4f0e7';
const muted = '#9eb2bf';
const cyan = '#49d5c8';
const amber = '#ffb14a';
const red = '#ff5d5d';

const stringParam = (state: EditState, key: string, fallback = ''): string => {
  const value = state.parameters[key];
  return typeof value === 'string' ? value : fallback;
};
const numberParam = (state: EditState, key: string, fallback = 0): number => {
  const value = state.parameters[key];
  return typeof value === 'number' ? value : fallback;
};
const arrayParam = <T,>(state: EditState, key: string): T[] => {
  const value = state.parameters[key];
  return Array.isArray(value) ? value as T[] : [];
};

const activeState = (states: EditState[], frame: number): EditState => {
  const ordered = [...states].sort((a, b) => a.at_frame - b.at_frame);
  return ordered.filter((row) => row.at_frame <= frame).at(-1) ?? ordered[0] ?? {
    decision_id: 'fallback', at_frame: 0, operation: 'KINETIC_TEXT', primary_visual_change: true,
    narrative_purpose: 'Fallback visual', parameters: {},
  };
};

const stateProgress = (state: EditState, states: EditState[], frame: number, totalFrames: number): number => {
  const next = [...states].filter((row) => row.at_frame > state.at_frame).sort((a, b) => a.at_frame - b.at_frame)[0];
  const end = next?.at_frame ?? totalFrames;
  return interpolate(frame, [state.at_frame, Math.max(state.at_frame + 1, end)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
};

const Background: React.FC<{portrait: boolean}> = ({portrait}) => (
  <AbsoluteFill style={{background: `radial-gradient(circle at ${portrait ? '80% 12%' : '72% 22%'}, #143449 0, ${navy} 46%, #030a0f 100%)`}}>
    <AbsoluteFill style={{opacity: 0.12, backgroundImage: 'linear-gradient(rgba(114,186,196,.16) 1px, transparent 1px), linear-gradient(90deg, rgba(114,186,196,.16) 1px, transparent 1px)', backgroundSize: portrait ? '54px 54px' : '72px 72px'}} />
    <AbsoluteFill style={{opacity: 0.075, backgroundImage: 'repeating-radial-gradient(circle at 13px 9px, #fff 0 0.8px, transparent 0.9px 5px)'}} />
  </AbsoluteFill>
);

const PhotoVisual: React.FC<{state: EditState; progress: number}> = ({state, progress}) => {
  const zoom = 1.04 + progress * 0.09 + numberParam(state, 'zoom_bias', 0);
  const focusX = numberParam(state, 'focus_x', 50);
  const focusY = numberParam(state, 'focus_y', 50);
  const source = state.asset_path ? staticFile(state.asset_path.replaceAll('\\', '/')) : null;
  return <AbsoluteFill>
    {source ? <Img src={source} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: `${focusX}% ${focusY}%`, transform: `scale(${zoom})`, filter: 'saturate(.78) contrast(1.08) brightness(.77)'}} /> : null}
    <AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(3,10,15,.92) 0%, rgba(3,10,15,.16) 58%, rgba(3,10,15,.62) 100%)'}} />
    <AbsoluteFill style={{background: 'linear-gradient(0deg, rgba(3,10,15,.94) 0%, transparent 48%, rgba(3,10,15,.45) 100%)'}} />
  </AbsoluteFill>;
};

const DocumentVisual: React.FC<{state: EditState; portrait: boolean; progress: number}> = ({state, portrait, progress}) => {
  const lines = arrayParam<string>(state, 'document_lines');
  const active = Math.min(lines.length - 1, Math.max(0, Math.floor(progress * Math.max(1, lines.length))));
  return <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', padding: portrait ? '18% 7% 24%' : '8% 15% 13%'}}>
    <div style={{width: portrait ? '92%' : '82%', height: portrait ? '72%' : '78%', background: '#f4efe5', color: '#13222a', boxShadow: '0 28px 80px rgba(0,0,0,.48)', transform: `perspective(1200px) rotateY(${portrait ? -2 : -5}deg) scale(${0.96 + progress * .035})`, padding: portrait ? 56 : 68, position: 'relative', overflow: 'hidden'}}>
      <div style={{display: 'flex', justifyContent: 'space-between', color: '#4d6471', fontSize: portrait ? 24 : 28, fontWeight: 800, letterSpacing: 2}}>
        <span>U.S. ENERGY INFORMATION ADMINISTRATION</span><span>{stringParam(state, 'document_date', 'OFFICIAL RELEASE')}</span>
      </div>
      <div style={{height: 7, width: '28%', background: cyan, margin: '28px 0 34px'}} />
      <div style={{fontSize: portrait ? 48 : 58, lineHeight: 1.04, fontWeight: 900, letterSpacing: -2, maxWidth: '94%'}}>{stringParam(state, 'document_title', 'Official source record')}</div>
      <div style={{marginTop: portrait ? 44 : 34, display: 'grid', gap: portrait ? 28 : 18}}>
        {(lines.length ? lines : ['Evidence-bound source excerpt']).map((line, index) => <div key={line + index} style={{fontSize: portrait ? 32 : 34, lineHeight: 1.25, padding: '12px 18px', background: index === active ? 'rgba(255,177,74,.33)' : 'transparent', borderLeft: index === active ? `7px solid ${amber}` : '7px solid transparent', opacity: index <= active ? 1 : .42, transform: `translateX(${index <= active ? 0 : 18}px)`}}>{line}</div>)}
      </div>
      <div style={{position: 'absolute', bottom: 24, right: 34, color: '#6e8089', fontSize: 22}}>SOURCE DOCUMENT • PUNCH-IN / HIGHLIGHT</div>
    </div>
  </AbsoluteFill>;
};

type MapPoint = {x: number; y: number; label: string};
const MapVisual: React.FC<{state: EditState; portrait: boolean; progress: number}> = ({state, portrait, progress}) => {
  const points = arrayParam<MapPoint>(state, 'map_points');
  const route = points.map((point) => `${point.x},${point.y}`).join(' ');
  return <AbsoluteFill style={{padding: portrait ? '18% 6% 25%' : '10% 11% 12%'}}>
    <svg viewBox="0 0 1000 620" style={{width: '100%', height: '100%', overflow: 'visible'}}>
      <defs>
        <linearGradient id="sea" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#0c3544"/><stop offset="1" stopColor="#061b28"/></linearGradient>
        <filter id="glow"><feGaussianBlur stdDeviation="5" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <rect width="1000" height="620" rx="30" fill="url(#sea)"/>
      <path d="M0 94 C160 90 250 145 356 132 C486 115 520 50 665 68 C790 84 852 142 1000 124 L1000 0 L0 0Z" fill="#526254" opacity=".72"/>
      <path d="M0 620 L0 468 C155 430 275 468 396 420 C520 370 606 426 716 370 C844 306 902 338 1000 300 L1000 620Z" fill="#7a694a" opacity=".74"/>
      <path d="M705 80 C734 162 742 246 700 329 C674 380 699 416 757 425 C821 436 875 401 1000 380" fill="none" stroke="#a29370" strokeWidth="30" opacity=".48"/>
      {route ? <polyline points={route} fill="none" stroke={cyan} strokeWidth="8" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="1200" strokeDashoffset={1200 * (1 - progress)} filter="url(#glow)"/> : null}
      {points.map((point, index) => {
        const visible = progress >= index / Math.max(1, points.length);
        return <g key={point.label} opacity={visible ? 1 : 0} transform={`translate(${point.x} ${point.y})`}>
          <circle r="14" fill={index === points.length - 1 ? amber : cyan}/><circle r="28" fill="none" stroke={index === points.length - 1 ? amber : cyan} opacity=".35" strokeWidth="3"/>
          <text x="22" y="-18" fill={ink} fontSize="30" fontWeight="800">{point.label}</text>
        </g>;
      })}
      <text x="52" y="566" fill={muted} fontSize="25" letterSpacing="3">DETERMINISTIC CONTEXT MAP • NOT LIVE TRAFFIC</text>
    </svg>
  </AbsoluteFill>;
};

type TimelineItem = {date: string; label: string};
const TimelineVisual: React.FC<{state: EditState; portrait: boolean; progress: number}> = ({state, portrait, progress}) => {
  const items = arrayParam<TimelineItem>(state, 'timeline_items');
  const visible = Math.max(1, Math.ceil(progress * items.length));
  return <AbsoluteFill style={{padding: portrait ? '20% 8% 27%' : '13% 10% 14%', justifyContent: 'center'}}>
    <div style={{fontSize: portrait ? 30 : 28, letterSpacing: 5, color: cyan, fontWeight: 800, marginBottom: 44}}>WHAT CHANGED — AND WHAT COMES NEXT</div>
    <div style={{display: 'grid', gridTemplateColumns: portrait ? '1fr' : `repeat(${Math.max(1, items.length)}, 1fr)`, gap: portrait ? 22 : 18, position: 'relative'}}>
      {!portrait ? <div style={{position: 'absolute', height: 5, background: `linear-gradient(90deg, ${cyan} ${progress * 100}%, #24404b ${progress * 100}%)`, left: '6%', right: '6%', top: 44}} /> : null}
      {items.map((item, index) => <div key={item.date} style={{opacity: index < visible ? 1 : .25, transform: `translate${portrait ? 'X' : 'Y'}(${index < visible ? 0 : 20}px)`, padding: portrait ? '22px 28px' : '80px 20px 24px', borderLeft: portrait ? `5px solid ${index < visible ? cyan : '#2b4652'}` : undefined, background: portrait ? 'rgba(11,34,46,.72)' : undefined, position: 'relative'}}>
        {!portrait ? <div style={{position: 'absolute', top: 30, left: '50%', width: 26, height: 26, borderRadius: 20, background: index < visible ? cyan : '#2b4652', transform: 'translateX(-50%)'}}/> : null}
        <div style={{fontSize: portrait ? 31 : 28, color: amber, fontWeight: 900}}>{item.date}</div>
        <div style={{fontSize: portrait ? 38 : 34, color: ink, fontWeight: 800, lineHeight: 1.08, marginTop: 10}}>{item.label}</div>
      </div>)}
    </div>
  </AbsoluteFill>;
};

type ComparisonItem = {label: string; value: string; note?: string; tone?: string};
const ComparisonVisual: React.FC<{state: EditState; portrait: boolean; progress: number}> = ({state, portrait, progress}) => {
  const items = arrayParam<ComparisonItem>(state, 'comparison_items');
  return <AbsoluteFill style={{padding: portrait ? '18% 7% 26%' : '12% 10% 13%', justifyContent: 'center'}}>
    <div style={{fontSize: portrait ? 30 : 28, letterSpacing: 5, color: muted, fontWeight: 800, marginBottom: 42}}>{stringParam(state, 'kicker', 'THE FORECAST PATH')}</div>
    <div style={{display: 'grid', gridTemplateColumns: portrait ? '1fr' : `repeat(${Math.max(1, items.length)}, 1fr)`, gap: portrait ? 18 : 26}}>
      {items.map((item, index) => {const reveal = interpolate(progress, [index / Math.max(1, items.length), (index + 1) / Math.max(1, items.length)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}); return <div key={item.label} style={{minHeight: portrait ? 178 : 300, padding: portrait ? '26px 34px' : '36px 38px', borderTop: `8px solid ${item.tone === 'risk' ? red : index === items.length - 1 ? cyan : amber}`, background: 'linear-gradient(145deg, rgba(20,52,69,.92), rgba(7,20,31,.72))', transform: `translateY(${(1-reveal)*34}px) scale(${.96 + reveal*.04})`, opacity: .16 + .84*reveal}}>
          <div style={{fontSize: portrait ? 27 : 28, color: muted, fontWeight: 800, letterSpacing: 2}}>{item.label}</div>
          <div style={{fontSize: portrait ? 76 : 92, color: ink, fontWeight: 950, letterSpacing: -4, lineHeight: 1.05, marginTop: 12}}>{item.value}</div>
          {item.note ? <div style={{fontSize: portrait ? 25 : 25, color: '#c8d5d9', lineHeight: 1.25, marginTop: 14}}>{item.note}</div> : null}
        </div>;})}
    </div>
  </AbsoluteFill>;
};

const ChartVisual: React.FC<{state: EditState; portrait: boolean; progress: number}> = ({state, portrait, progress}) => {
  const source = state.asset_path ? staticFile(state.asset_path.replaceAll('\\', '/')) : null;
  const reveal = Math.max(5, progress * 100);
  return <AbsoluteFill style={{padding: portrait ? '17% 3% 25%' : '9% 6% 12%', justifyContent: 'center'}}>
    <div style={{position: 'relative', width: '100%', height: portrait ? '56%' : '82%', background: '#f9f7f2', boxShadow: '0 30px 90px rgba(0,0,0,.44)', overflow: 'hidden'}}>
      {source ? <Img src={source} style={portrait ? {
        position: 'absolute', left: `${-55 * progress}%`, top: 0, width: '155%', height: '100%', objectFit: 'contain',
        filter: 'contrast(1.08) saturate(.92)',
      } : {width: '100%', height: '100%', objectFit: 'contain', clipPath: `inset(0 ${100-reveal}% 0 0)`, filter: 'contrast(1.02) saturate(.9)'}}/> : null}
      <div style={{position: 'absolute', top: 0, bottom: 0, left: portrait ? `${18 + progress * 64}%` : `${Math.min(97, reveal)}%`, width: portrait ? 5 : 4, background: cyan, boxShadow: `0 0 24px ${cyan}`}}/>
      <div style={{position: 'absolute', right: portrait ? 18 : 30, top: portrait ? 20 : 28, background: 'rgba(7,20,31,.92)', color: ink, padding: portrait ? '20px 22px' : '18px 24px', maxWidth: portrait ? '58%' : '38%'}}>
        <div style={{fontSize: portrait ? 25 : 22, color: cyan, fontWeight: 900, letterSpacing: 3}}>{portrait ? 'MOBILE CHART REFRAME' : 'SOURCE-BACKED CHART'}</div>
        <div style={{fontSize: portrait ? 35 : 34, fontWeight: 850, lineHeight: 1.08, marginTop: 10}}>{stringParam(state, 'annotation', 'Read the endpoint, then the path.')}</div>
      </div>
    </div>
    {portrait ? <div style={{marginTop: 24, color: muted, fontSize: 25, letterSpacing: 2}}>PAN: AXIS → PATH → LATEST OBSERVATION</div> : null}
  </AbsoluteFill>;
};

type MechanismNode = {label: string; note?: string};
const MechanismVisual: React.FC<{state: EditState; portrait: boolean; progress: number}> = ({state, portrait, progress}) => {
  const nodes = arrayParam<MechanismNode>(state, 'mechanism_nodes');
  return <AbsoluteFill style={{padding: portrait ? '18% 8% 27%' : '12% 8% 14%', justifyContent: 'center'}}>
    <div style={{fontSize: portrait ? 30 : 28, letterSpacing: 5, color: cyan, fontWeight: 800, marginBottom: 40}}>THE MECHANISM — NOT A PREDICTION</div>
    <div style={{display: 'flex', flexDirection: portrait ? 'column' : 'row', alignItems: 'stretch', gap: portrait ? 14 : 24}}>
      {nodes.map((node, index) => {const reveal = interpolate(progress, [index / Math.max(1, nodes.length), Math.min(1, (index + .72) / Math.max(1, nodes.length))], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}); return <React.Fragment key={node.label}>
        <div style={{flex: 1, minHeight: portrait ? 118 : 260, padding: portrait ? '24px 30px' : '38px 34px', background: `linear-gradient(145deg, rgba(26,73,87,${.35 + reveal * .59}), rgba(9,30,41,.94))`, border: `2px solid rgba(73,213,200,${.18 + reveal * .62})`, opacity: .22 + reveal * .78, transform: `translate${portrait ? 'X' : 'Y'}(${(1-reveal)*24}px) scale(${.94 + reveal*.06})`}}>
          <div style={{fontSize: portrait ? 37 : 38, color: ink, fontWeight: 900, lineHeight: 1.05}}>{node.label}</div>
          {node.note ? <div style={{fontSize: portrait ? 24 : 24, color: muted, marginTop: 16, lineHeight: 1.25}}>{node.note}</div> : null}
        </div>
        {index < nodes.length - 1 ? <div style={{alignSelf: 'center', color: reveal > .72 ? amber : '#314a55', fontSize: portrait ? 38 : 54, fontWeight: 900, transform: `${portrait ? 'rotate(90deg)' : ''} scale(${.7 + reveal*.3})`, opacity: .25 + reveal*.75}}>→</div> : null}
      </React.Fragment>;})}
    </div>
  </AbsoluteFill>;
};

const KineticMotif: React.FC<{state: EditState; portrait: boolean; progress: number}> = ({state, portrait, progress}) => {
  const kind = state.asset_class || 'editorial';
  const photo = state.asset_path ? staticFile(state.asset_path.replaceAll('\\', '/')) : null;
  if (photo) return <AbsoluteFill>
    <Img src={photo} style={{width:'100%',height:'100%',objectFit:'cover',transform:`scale(${1.06 + progress*.1})`,filter:'brightness(.36) saturate(.72)'}}/>
    <AbsoluteFill style={{background:'linear-gradient(90deg,rgba(3,10,15,.92),rgba(3,10,15,.2),rgba(3,10,15,.8))'}}/>
  </AbsoluteFill>;
  if (kind === 'deterministic_comparison') return <div style={{position:'absolute',right:portrait?'6%':'7%',top:portrait?'19%':'20%',width:portrait?'48%':'42%',display:'grid',gap:portrait?22:28,opacity:.62}}>
    {[.92,.68,.48].map((size,index)=><div key={size} style={{height:portrait?82:96,border:`2px solid ${index===2?cyan:amber}`,background:'rgba(13,43,56,.72)',transform:`translateX(${(1-progress)*(80+index*35)}px)`,width:`${size*100}%`,justifySelf:'end'}}/>)}</div>;
  if (kind === 'official_source_document') return <div style={{position:'absolute',right:portrait?'5%':'8%',top:portrait?'17%':'14%',width:portrait?'58%':'39%',height:portrait?'48%':'64%',background:'rgba(244,239,229,.12)',border:'2px solid rgba(244,239,229,.24)',transform:`perspective(900px) rotateY(${-8+progress*4}deg) translateX(${(1-progress)*55}px)`,padding:30}}>
    {[.72,.9,.64,.82,.54].map((size,index)=><div key={index} style={{height:8,marginBottom:24,width:`${size*100}%`,background:index===2?amber:'rgba(244,239,229,.3)'}}/>)}</div>;
  if (kind === 'deterministic_map') return <svg viewBox="0 0 700 420" style={{position:'absolute',right:portrait?'-18%':'3%',top:portrait?'17%':'19%',width:portrait?'95%':'54%',opacity:.55}}><path d="M40 298 C180 112 335 355 640 92" fill="none" stroke="#315769" strokeWidth="34"/><path d="M40 298 C180 112 335 355 640 92" fill="none" stroke={cyan} strokeWidth="7" strokeDasharray="950" strokeDashoffset={950*(1-progress)}/><circle cx={40+600*progress} cy={298-206*progress} r="13" fill={amber}/></svg>;
  if (kind === 'deterministic_diagram') return <div style={{position:'absolute',right:portrait?'5%':'6%',top:portrait?'17%':'24%',width:portrait?'68%':'48%',display:'flex',flexDirection:portrait?'column':'row',gap:18,opacity:.56}}>{['FLOW','OUTPUT','STOCKS'].map((label,index)=><div key={label} style={{flex:1,padding:24,border:`2px solid ${cyan}`,background:'rgba(14,48,61,.76)',transform:`translate${portrait?'X':'Y'}(${Math.max(0,(index/3-progress))*90}px)`,opacity:progress>=index/3?1:.18,fontSize:22,fontWeight:900,color:ink}}>{label}</div>)}</div>;
  if (kind === 'deterministic_timeline') return <div style={{position:'absolute',left:portrait?'9%':'44%',right:'7%',top:portrait?'23%':'28%',height:6,background:'#284652',opacity:.72}}><div style={{width:`${progress*100}%`,height:'100%',background:cyan}}/>{[0,33,66,100].map(value=><div key={value} style={{position:'absolute',left:`${value}%`,top:-11,width:28,height:28,borderRadius:30,background:progress*100>=value?amber:'#284652'}}/>)}</div>;
  return <svg viewBox="0 0 800 420" style={{position:'absolute',right:'2%',top:portrait?'21%':'20%',width:portrait?'88%':'56%',opacity:.42}}><polyline points="20,345 120,278 210,315 315,180 405,228 520,92 635,146 780,48" fill="none" stroke={cyan} strokeWidth="9" strokeDasharray="1300" strokeDashoffset={1300*(1-progress)}/></svg>;
};

const KineticVisual: React.FC<{state: EditState; portrait: boolean; progress: number}> = ({state, portrait, progress}) => {
  const headline = stringParam(state, 'headline', stringParam(state, 'title', 'THE EVIDENCE CHANGED'));
  const subline = stringParam(state, 'subline', 'Now follow the mechanism.');
  const words = headline.split(' ');
  return <AbsoluteFill style={{padding: portrait ? '18% 8% 28%' : '12% 9% 15%', justifyContent: 'center'}}>
    <KineticMotif state={state} portrait={portrait} progress={progress}/>
    <div style={{fontSize: portrait ? 25 : 25, color: cyan, fontWeight: 900, letterSpacing: 5, marginBottom: 30,position:'relative'}}>{stringParam(state, 'kicker', 'CAPITAL CHRONICLE • EVIDENCE BOUND')}</div>
    <div style={{maxWidth: portrait ? '96%' : '85%', fontSize: portrait ? 98 : 126, lineHeight: .91, fontWeight: 950, letterSpacing: portrait ? -5 : -7, color: ink,position:'relative',textShadow:'0 5px 30px rgba(0,0,0,.62)'}}>
      {words.map((word, index) => {const reveal = interpolate(progress, [index/Math.max(1,words.length), (index+1)/Math.max(1,words.length)], [0,1], {extrapolateLeft:'clamp', extrapolateRight:'clamp'}); return <span key={word+index} style={{display:'inline-block', marginRight: '.22em', opacity: reveal, transform: `translateY(${(1-reveal)*34}px)`, color: word.includes('$') || word.match(/\d/) ? amber : undefined}}>{word}</span>;})}
    </div>
    <div style={{fontSize: portrait ? 36 : 43, lineHeight: 1.2, color: muted, maxWidth: portrait ? '92%' : '70%', marginTop: 36, borderLeft: `6px solid ${amber}`, paddingLeft: 24,position:'relative',textShadow:'0 4px 22px rgba(0,0,0,.72)'}}>{subline}</div>
  </AbsoluteFill>;
};

const VisualStage: React.FC<{state: EditState; states: EditState[]; portrait: boolean; frame: number; totalFrames: number}> = ({state, states, portrait, frame, totalFrames}) => {
  const progress = stateProgress(state, states, frame, totalFrames);
  switch (state.operation) {
    case 'LOCATION_CUTAWAY': case 'REFRAME': case 'PUNCH_IN': return <PhotoVisual state={state} progress={progress}/>;
    case 'DOCUMENT_FOCUS': case 'SOURCE_HIGHLIGHT': return <DocumentVisual state={state} portrait={portrait} progress={progress}/>;
    case 'MAP_TRACE': return <MapVisual state={state} portrait={portrait} progress={progress}/>;
    case 'TIMELINE_STEP': return <TimelineVisual state={state} portrait={portrait} progress={progress}/>;
    case 'COMPARISON_REVEAL': return <ComparisonVisual state={state} portrait={portrait} progress={progress}/>;
    case 'CHART_TRACE': case 'POINT_ANNOTATION': return <ChartVisual state={state} portrait={portrait} progress={progress}/>;
    case 'MECHANISM_FLOW': return <MechanismVisual state={state} portrait={portrait} progress={progress}/>;
    case 'PAYOFF_REVEAL': case 'KINETIC_TEXT': case 'CUT': case 'WIPE_TRANSITION': default: return <KineticVisual state={state} portrait={portrait} progress={progress}/>;
  }
};

const CaptionLayer: React.FC<{job: BeatRenderJob; frame: number; portrait: boolean}> = ({job, frame, portrait}) => {
  if (!job.captions_visible) return null;
  const cue = job.caption_cues.find((row) => row.start_frame <= frame && frame < row.end_frame);
  if (!cue) return null;
  const enter = interpolate(frame, [cue.start_frame, cue.start_frame + 5], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <div style={{position: 'absolute', left: `${job.caption_layout.left * 100}%`, right: `${job.caption_layout.right * 100}%`, bottom: `${job.caption_layout.bottom * 100}%`, display: 'flex', justifyContent: 'center', zIndex: 20, opacity: enter, transform: `translateY(${(1-enter)*18}px)`}}>
    <div style={{background: 'rgba(2,9,14,.88)', boxShadow: '0 8px 35px rgba(0,0,0,.36)', padding: portrait ? '17px 25px 20px' : '12px 22px 15px', borderBottom: `5px solid ${cyan}`, maxWidth: portrait ? '96%' : '82%', textAlign: 'center'}}>
      {cue.lines.slice(0,2).map((line, index) => <div key={line+index} style={{fontSize: portrait ? 43 : 35, fontWeight: 850, color: ink, lineHeight: 1.08, letterSpacing: -.6}}>{line}</div>)}
    </div>
  </div>;
};

const Chrome: React.FC<{job: BeatRenderJob; portrait: boolean; state: EditState}> = ({job, portrait, state}) => <>
  <div style={{position: 'absolute', top: portrait ? '5.1%' : '4.5%', left: portrait ? '6.5%' : '5.5%', display: 'flex', alignItems: 'center', gap: 15, zIndex: 30}}>
    <div style={{width: portrait ? 14 : 12, height: portrait ? 14 : 12, borderRadius: 20, background: amber, boxShadow: `0 0 18px ${amber}`}}/>
    <div style={{fontSize: portrait ? 24 : 22, letterSpacing: 5, color: ink, fontWeight: 900}}>CAPITAL CHRONICLE</div>
  </div>
  <div style={{position: 'absolute', top: portrait ? '9%' : '5%', right: portrait ? '6.5%' : '5.5%', color: muted, fontSize: portrait ? 20 : 18, letterSpacing: 2, fontWeight: 700, zIndex: 30, textAlign: 'right'}}>{job.chapter_id.toUpperCase()}<br/><span style={{color: cyan}}>{job.narrative_role.toUpperCase()}</span></div>
  <div style={{position: 'absolute', left: portrait ? '6.5%' : '5.5%', bottom: portrait ? '4.6%' : '3.3%', right: portrait ? '6.5%' : '5.5%', color: '#90a5af', fontSize: portrait ? 18 : 16, zIndex: 30, display: 'flex', justifyContent: 'space-between', gap: 20}}>
    <span>{state.attribution || job.source_label}</span><span>{job.beat_id}</span>
  </div>
</>;

export const RetentionNativeBeat: React.FC<{job: BeatRenderJob}> = ({job}) => {
  const frame = useCurrentFrame();
  const config = useVideoConfig();
  const portrait = config.height > config.width;
  const state = activeState(job.edit_states, frame);
  const changePulse = interpolate(frame - state.at_frame, [0, 4, 11], [0.24, 0.06, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const introWipe = interpolate(frame, [0, 9], [100, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const outro = interpolate(frame, [config.durationInFrames - 7, config.durationInFrames - 1], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{fontFamily: 'Arial, Helvetica, sans-serif', background: navy, color: ink, overflow: 'hidden'}}>
    <Background portrait={portrait}/>
    <VisualStage state={state} states={job.edit_states} portrait={portrait} frame={frame} totalFrames={config.durationInFrames}/>
    <AbsoluteFill style={{background: cyan, opacity: changePulse, mixBlendMode: 'screen', pointerEvents: 'none'}}/>
    <Chrome job={job} portrait={portrait} state={state}/>
    <CaptionLayer job={job} frame={frame} portrait={portrait}/>
    <div style={{position: 'absolute', inset: 0, background: cyan, transform: `translateX(-${introWipe}%)`, opacity: frame < 10 ? .36 : 0, zIndex: 50}}/>
    <AbsoluteFill style={{background: navy, opacity: outro, zIndex: 60}}/>
  </AbsoluteFill>;
};
