import React from 'react';
import {AbsoluteFill, Audio, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {accent, color, easeInOut, face, progress} from './motion';
import type {SceneJob, Series} from './types';

const margin = (job: SceneJob) => job.width * (job.aspect === 'vertical' ? 0.075 : 0.064);
const titleSize = (job: SceneJob, scale = 1) => job.height * (job.aspect === 'vertical' ? 0.064 : 0.083) * scale;

const Brand: React.FC<{job: SceneJob; inverse?: boolean}> = ({job, inverse = false}) => (
  <div style={{position: 'absolute', left: margin(job), right: margin(job), top: job.height * 0.038, display: 'flex', alignItems: 'center', justifyContent: 'space-between', zIndex: 30, color: inverse ? color.white : color.ink}}>
    <div style={{display: 'flex', alignItems: 'center', gap: job.width * 0.012}}>
      <div style={{width: job.height * 0.014, height: job.height * 0.014, background: accent(job.accent)}} />
      <span style={{fontFamily: face.display, fontSize: job.height * 0.022, fontWeight: 700, letterSpacing: '0.18em'}}>CAPITAL CHRONICLE</span>
    </div>
    <span style={{fontFamily: face.mono, fontSize: job.height * 0.016, opacity: 0.68}}>{job.chapter_id.toUpperCase()}</span>
  </div>
);

const Source: React.FC<{job: SceneJob; inverse?: boolean}> = ({job, inverse = false}) => (
  <div style={{position: 'absolute', left: margin(job), right: margin(job), bottom: job.height * (job.aspect === 'vertical' ? 0.018 : 0.034), display: 'flex', flexDirection: job.aspect === 'vertical' || job.source_compact ? 'column' : 'row', alignItems: job.aspect === 'vertical' ? 'flex-start' : 'initial', justifyContent: 'space-between', gap: job.aspect === 'vertical' ? 3 : 24, zIndex: 30, fontFamily: face.mono, fontSize: job.height * (job.aspect === 'vertical' ? 0.011 : 0.015), lineHeight: 1.2, color: inverse ? 'rgba(251,250,246,.72)' : 'rgba(11,11,12,.62)'}}>
    <span style={{maxWidth: job.aspect === 'vertical' ? '100%' : '74%'}}>{job.source_label}</span>
    {job.rights_label ? <span style={{textAlign: job.aspect === 'vertical' ? 'left' : 'right', maxWidth: '100%'}}>{job.rights_label}</span> : null}
  </div>
);

const Captions: React.FC<{job: SceneJob}> = ({job}) => {
  const frame = useCurrentFrame();
  const cue = job.captions.find((row) => frame >= row.start_frame && frame < row.end_frame);
  if (!cue) return null;
  const p = progress(frame, cue.start_frame, 5);
  return (
    <div style={{position: 'absolute', left: margin(job), right: margin(job), bottom: job.height * (job.aspect === 'vertical' ? 0.095 : 0.082), zIndex: 40, display: 'flex', justifyContent: 'center'}}>
      <div style={{background: 'rgba(11,11,12,.9)', color: color.white, borderLeft: `5px solid ${accent(job.accent)}`, padding: `${job.height * 0.012}px ${job.width * 0.018}px`, fontFamily: face.display, fontSize: job.height * (job.aspect === 'vertical' ? 0.030 : 0.028) * (job.caption_scale ?? 1), fontWeight: 650, lineHeight: 1.12, maxWidth: job.aspect === 'vertical' ? '94%' : '72%', opacity: p, transform: `translateY(${(1-p) * 10}px)`}}>{cue.text}</div>
    </div>
  );
};

const Kicker: React.FC<{job: SceneJob; inverse?: boolean}> = ({job, inverse = false}) => {
  const frame = useCurrentFrame();
  const p = progress(frame, 5, 18);
  return job.kicker ? <div style={{fontFamily: face.mono, fontWeight: 700, fontSize: job.height * 0.02, letterSpacing: '0.16em', color: inverse ? color.white : accent(job.accent), opacity: p, transform: `translateX(${(1-p) * -18}px)`, marginBottom: job.height * 0.02}}>{job.kicker.toUpperCase()}</div> : null;
};

const Headline: React.FC<{job: SceneJob; inverse?: boolean; scale?: number}> = ({job, inverse = false, scale = 1}) => {
  const frame = useCurrentFrame();
  const p = progress(frame, 10, 22);
  return <h1 style={{fontFamily: face.display, fontSize: titleSize(job, scale * (job.title_scale ?? 1)), lineHeight: 0.94, letterSpacing: '-0.045em', fontWeight: 760, color: inverse ? color.white : color.ink, margin: 0, opacity: p, transform: `translateY(${(1-p) * 24}px)`, maxWidth: job.aspect === 'vertical' ? '100%' : '88%', textWrap: 'balance'}}>{job.title}</h1>;
};

const Asset: React.FC<{job: SceneJob; fit?: 'cover' | 'contain'; style?: React.CSSProperties}> = ({job, fit = 'cover', style}) => {
  const frame = useCurrentFrame();
  if (!job.asset_path) return null;
  const p = progress(frame, 4, 24);
  const x = interpolate(progress(frame, 0, Math.max(1, job.duration_in_frames), easeInOut), [0, 1], [-1.2, 1.2]);
  return <Img src={staticFile(job.asset_path)} style={{width: '100%', height: '100%', objectFit: fit, opacity: p, transform: `translateX(${x}%) scale(1.015)`, ...style}} />;
};

const Plot: React.FC<{job: SceneJob; series: Series[]; compact?: boolean}> = ({job, series, compact = false}) => {
  const frame = useCurrentFrame();
  const w = job.width * (job.aspect === 'vertical' ? 0.82 : 0.70);
  const h = job.height * (compact ? 0.28 : job.aspect === 'vertical' ? 0.40 : 0.50);
  const padX = w * 0.05; const padY = h * 0.1;
  const values = series.flatMap((row) => row.points.map((point) => point.value));
  const min = Math.min(...values); const max = Math.max(...values); const span = max - min || 1;
  const longest = Math.max(...series.map((row) => row.points.length), 2);
  const x = (i: number) => padX + i / (longest - 1) * (w - padX * 2);
  const y = (v: number) => padY + (1 - (v - min) / span) * (h - padY * 2);
  const reveal = progress(frame, 12, 38, easeInOut);
  return <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{overflow: 'visible'}}>
    {[0, .25, .5, .75, 1].map((n) => <line key={n} x1={padX} x2={w-padX} y1={padY+n*(h-padY*2)} y2={padY+n*(h-padY*2)} stroke="rgba(11,11,12,.12)" strokeWidth={1} />)}
    {series.map((row, ri) => {
      const points = row.points.map((point, i) => `${x(i)},${y(point.value)}`).join(' ');
      const hue = row.color || [color.signal, color.cobalt, color.ink][ri % 3];
      return <g key={row.label}>
        <polyline points={points} fill="none" stroke={hue} strokeWidth={compact ? 4 : 6} strokeLinejoin="round" strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1-reveal} />
        {row.points.map((point, i) => <circle key={i} cx={x(i)} cy={y(point.value)} r={i === row.points.length-1 ? 7*reveal : 0} fill={hue} />)}
      </g>;
    })}
    {job.show_legend && series.length > 1 ? series.map((row, index) => <g key={`legend-${row.label}`}>
      <rect x={padX + index * w * 0.18} y={0} width={22} height={6} fill={row.color || [color.signal, color.cobalt, color.ink][index % 3]} />
      <text x={padX + 30 + index * w * 0.18} y={8} fontFamily={face.mono} fontSize={job.height * 0.016} fill={color.ink}>{row.label}</text>
    </g>) : null}
    <text x={padX} y={h + job.height * 0.025} fontFamily={face.mono} fontSize={job.height * 0.017} fill="rgba(11,11,12,.62)">{series[0]?.points[0]?.label}</text>
    <text x={w-padX} y={h + job.height * 0.025} textAnchor="end" fontFamily={face.mono} fontSize={job.height * 0.017} fill="rgba(11,11,12,.62)">{series[0]?.points.at(-1)?.label}</text>
  </svg>;
};

const ColdOpen: React.FC<{job: SceneJob}> = ({job}) => {
  const frame = useCurrentFrame(); const line = progress(frame, 18, 30, easeInOut);
  return <AbsoluteFill style={{background: color.ink, color: color.white}}><Brand job={job} inverse />
    <div style={{position: 'absolute', left: margin(job), right: margin(job), top: job.height * .19, bottom: job.height * .18, display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
      <Kicker job={job} inverse /><Headline job={job} inverse scale={1.18}/>
      <div style={{height: 6, width: `${line * 48}%`, background: accent(job.accent), marginTop: job.height * .04}}/>
      {job.deck ? <p style={{fontFamily: face.editorial, fontSize: job.height * .036, lineHeight: 1.28, maxWidth: job.aspect === 'vertical' ? '96%' : '66%', margin: `${job.height*.035}px 0 0`, color: 'rgba(251,250,246,.72)', opacity: progress(frame, 28, 22)}}>{job.deck}</p> : null}
    </div><Source job={job} inverse /></AbsoluteFill>;
};

const ChapterRupture: React.FC<{job: SceneJob}> = ({job}) => {
  const frame = useCurrentFrame(); const sweep = progress(frame, 0, 25, easeInOut);
  return <AbsoluteFill style={{background: accent(job.accent), color: color.ink, overflow: 'hidden'}}>
    <div style={{position: 'absolute', inset: 0, background: color.paper, transform: `translateX(${sweep * 105 - 105}%)`}} />
    <div style={{position: 'absolute', left: margin(job), top: job.height*.16, fontFamily: face.display, fontWeight: 800, fontSize: job.height*(job.aspect==='vertical'?.34:.46), letterSpacing: '-.08em', lineHeight: .7, color: color.ink, opacity: .09}}>{job.chapter_number || '01'}</div>
    <div style={{position: 'absolute', left: margin(job), right: margin(job), bottom: job.height*.20}}><Kicker job={job}/><Headline job={job} scale={1.05}/>{job.deck ? <p style={{fontFamily: face.editorial, fontSize: job.height*.032, maxWidth: '64%', lineHeight: 1.25}}>{job.deck}</p>:null}</div>
    <Brand job={job}/><Source job={job}/>
  </AbsoluteFill>;
};

const Illustration: React.FC<{job: SceneJob}> = ({job}) => <AbsoluteFill style={{background: color.ink}}>
  <Asset job={job}/><div style={{position:'absolute',inset:0,background:'linear-gradient(90deg,rgba(11,11,12,.88) 0%,rgba(11,11,12,.30) 66%,rgba(11,11,12,.58) 100%)'}}/>
  <Brand job={job} inverse/><div style={{position:'absolute',left:margin(job),right:margin(job),top:job.height*.24}}><Kicker job={job} inverse/><Headline job={job} inverse scale={.98}/>{job.deck?<p style={{fontFamily:face.editorial,fontSize:job.height*.034,lineHeight:1.3,color:'rgba(251,250,246,.78)',maxWidth:job.aspect==='vertical'?'90%':'52%'}}>{job.deck}</p>:null}</div>
  <div style={{position:'absolute',right:margin(job),top:job.height*.15,padding:'8px 12px',background:accent(job.accent),fontFamily:face.mono,fontWeight:800,fontSize:job.height*.018}}>ILLUSTRATION</div><Source job={job} inverse/>
  </AbsoluteFill>;

const CurveMorph: React.FC<{job: SceneJob}> = ({job}) => <AbsoluteFill style={{background: color.paper}}><Brand job={job}/>
  <div style={{position:'absolute',left:margin(job),right:margin(job),top:job.height*.15,bottom:job.height*.15,display:'grid',gridTemplateColumns:job.aspect==='vertical'?'1fr':'0.34fr 0.66fr',gap:job.width*.035,alignItems:'center'}}>
    <div><Kicker job={job}/><Headline job={job} scale={.72}/>{job.deck?<p style={{fontFamily:face.editorial,fontSize:job.height*.029,lineHeight:1.3,color:'rgba(11,11,12,.67)'}}>{job.deck}</p>:null}</div>
    <div style={{display:'flex',justifyContent:'center'}}><Plot job={job} series={job.series||[]}/></div>
  </div><Source job={job}/></AbsoluteFill>;

const Timeline: React.FC<{job: SceneJob}> = ({job}) => <AbsoluteFill style={{background: color.white}}><Brand job={job}/>
  <div style={{position:'absolute',left:margin(job),right:margin(job),top:job.height*.14}}><Kicker job={job}/><Headline job={job} scale={.70}/></div>
  <div style={{position:'absolute',left:margin(job),right:margin(job),bottom:job.height*.17,display:'flex',justifyContent:'center'}}><Plot job={job} series={job.series||[]} compact/></div>
  <Source job={job}/></AbsoluteFill>;

const SourceEvidence: React.FC<{job: SceneJob}> = ({job}) => {
  const frame=useCurrentFrame(); const highlight=progress(frame,20,30,easeInOut);
  return <AbsoluteFill style={{background:color.ink,color:color.white}}><Brand job={job} inverse/>
    <div style={{position:'absolute',left:margin(job),top:job.height*.18,width:job.aspect==='vertical'?'84%':'36%',zIndex:4}}><Kicker job={job} inverse/><Headline job={job} inverse scale={.72}/>{job.deck?<p style={{fontFamily:face.editorial,fontSize:job.height*.029,lineHeight:1.3,color:'rgba(251,250,246,.7)'}}>{job.deck}</p>:null}</div>
    <div style={{position:'absolute',right:job.aspect==='vertical'?margin(job):job.width*.04,top:job.aspect==='vertical'?job.height*.46:job.height*.12,width:job.aspect==='vertical'?job.width-margin(job)*2:job.width*.49*(job.asset_scale??1),height:job.aspect==='vertical'?job.height*.36:job.height*.74,background:color.paper,boxShadow:'0 30px 90px rgba(0,0,0,.45)',overflow:'hidden'}}><Asset job={job} fit="contain"/><div style={{position:'absolute',left:0,right:0,top:`${30+highlight*34}%`,height:job.height*.045,background:'rgba(241,178,74,.32)',borderTop:`2px solid ${color.amber}`,borderBottom:`2px solid ${color.amber}`}}/></div>
    <Source job={job} inverse/></AbsoluteFill>;
};

const Comparison: React.FC<{job: SceneJob}> = ({job}) => {
  const frame=useCurrentFrame();
  return <AbsoluteFill style={{background:color.paper}}><Brand job={job}/><div style={{position:'absolute',left:margin(job),right:margin(job),top:job.height*.15}}><Kicker job={job}/><Headline job={job} scale={.62}/></div>
    <div style={{position:'absolute',left:margin(job),right:margin(job),top:job.height*.43,bottom:job.height*(job.aspect==='vertical'?.28:.14),display:'grid',gridTemplateColumns:job.aspect==='vertical'?'1fr':'repeat(3,1fr)',gap:job.width*.02}}>{(job.numbers||[]).slice(0,3).map((n,i)=>{const p=progress(frame,18+i*8,22);return <div key={n.label} style={{borderTop:`7px solid ${i===0?accent(job.accent):color.ink}`,paddingTop:job.height*.018,opacity:p,transform:`translateY(${(1-p)*18}px)`}}><div style={{fontFamily:face.display,fontWeight:800,fontSize:job.height*(job.aspect==='vertical'?.072:.095),letterSpacing:'-.05em'}}>{n.value}</div><div style={{fontFamily:face.mono,fontSize:job.height*.019,fontWeight:700,textTransform:'uppercase',letterSpacing:'.09em'}}>{n.label}</div>{n.note?<div style={{fontFamily:face.editorial,fontSize:job.height*.021,opacity:.62,marginTop:8}}>{n.note}</div>:null}</div>})}</div><Source job={job}/></AbsoluteFill>;
};

const Kinetic: React.FC<{job: SceneJob}> = ({job}) => {
  const frame=useCurrentFrame(); const words=(job.statement||job.title).split(' ');
  return <AbsoluteFill style={{background:color.ink,color:color.white}}><Brand job={job} inverse/><div style={{position:'absolute',left:margin(job),right:margin(job),top:job.height*.2,bottom:job.height*.18,display:'flex',alignContent:'center',alignItems:'center',flexWrap:'wrap',gap:`${job.height*.012}px ${job.width*.012}px`}}>{words.map((word,i)=>{const p=progress(frame,8+i*2.4,12);return <span key={i} style={{fontFamily:face.display,fontWeight:i%5===0?800:560,fontSize:job.height*(job.aspect==='vertical'?.075:.105),lineHeight:.9,letterSpacing:'-.055em',color:i%5===0?accent(job.accent):color.white,opacity:p,transform:`translateY(${(1-p)*26}px)`}}>{word}</span>})}</div><Source job={job} inverse/></AbsoluteFill>;
};

const Close: React.FC<{job: SceneJob}> = ({job}) => <AbsoluteFill style={{background:color.paperWarm}}><Brand job={job}/><div style={{position:'absolute',left:margin(job),right:margin(job),top:job.height*.22}}><Kicker job={job}/><Headline job={job} scale={.88}/>{job.deck?<p style={{fontFamily:face.editorial,fontSize:job.height*.035,lineHeight:1.3,maxWidth:'68%',color:'rgba(11,11,12,.7)'}}>{job.deck}</p>:null}{job.disclosure?<p style={{fontFamily:face.mono,fontSize:job.height*.019,lineHeight:1.35,maxWidth:'70%',borderTop:`3px solid ${accent(job.accent)}`,paddingTop:job.height*.018,marginTop:job.height*.04}}>{job.disclosure}</p>:null}</div><Source job={job}/></AbsoluteFill>;

const Portrait: React.FC<{job: SceneJob}> = ({job}) => <AbsoluteFill style={{background:color.white}}><div style={{position:'absolute',left:0,top:0,bottom:0,width:job.aspect==='vertical'?'100%':'52%'}}><Asset job={job}/></div><div style={{position:'absolute',inset:0,background:job.aspect==='vertical'?'linear-gradient(0deg,rgba(11,11,12,.95),transparent 68%)':'linear-gradient(90deg,transparent 35%,rgba(251,250,246,.96) 60%)'}}/><Brand job={job}/><div style={{position:'absolute',left:job.aspect==='vertical'?margin(job):job.width*.56,right:margin(job),bottom:job.height*.19}}><Kicker job={job}/><Headline job={job} scale={.76}/>{job.deck?<p style={{fontFamily:face.editorial,fontSize:job.height*.029,lineHeight:1.3}}>{job.deck}</p>:null}</div><Source job={job}/></AbsoluteFill>;

const MapField: React.FC<{job: SceneJob}> = ({job}) => <AbsoluteFill style={{background:color.paper}}><Asset job={job} fit="contain" style={{filter:'grayscale(1) contrast(1.12)',opacity:.68}}/><div style={{position:'absolute',inset:0,background:'linear-gradient(90deg,rgba(240,238,232,.96),rgba(240,238,232,.18))'}}/><Brand job={job}/><div style={{position:'absolute',left:margin(job),top:job.height*.22,width:job.aspect==='vertical'?'84%':'42%'}}><Kicker job={job}/><Headline job={job} scale={.75}/></div><Source job={job}/></AbsoluteFill>;

export const Scene: React.FC<{job: SceneJob}> = ({job}) => {
  let body: React.ReactNode;
  switch(job.primitive){
    case 'COLD_OPEN': body=<ColdOpen job={job}/>; break;
    case 'CHAPTER_RUPTURE': body=<ChapterRupture job={job}/>; break;
    case 'ILLUSTRATION_ATMOSPHERE': body=<Illustration job={job}/>; break;
    case 'CURVE_MORPH': body=<CurveMorph job={job}/>; break;
    case 'TIMELINE_TRACE': body=<Timeline job={job}/>; break;
    case 'SOURCE_EVIDENCE': body=<SourceEvidence job={job}/>; break;
    case 'COMPARISON_FIELD': body=<Comparison job={job}/>; break;
    case 'KINETIC_STATEMENT': body=<Kinetic job={job}/>; break;
    case 'BOUNDARY_CLOSE': body=<Close job={job}/>; break;
    case 'ENTITY_PORTRAIT': body=<Portrait job={job}/>; break;
    case 'MAP_FIELD': body=<MapField job={job}/>; break;
    default: throw new Error(`unsupported_primitive:${String(job.primitive)}`);
  }
  return <AbsoluteFill style={{overflow:'hidden'}}>{body}<Captions job={job}/>{job.narration_asset?<Audio src={staticFile(job.narration_asset)}/>:null}</AbsoluteFill>;
};
