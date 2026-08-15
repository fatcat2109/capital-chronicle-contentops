/* CODEX_VIEWER_FACING_AUTHORSHIP: material-rich editorial repair of the frozen Treasury story. */
import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame} from 'remotion';

const C={paper:'#f2ede2',paper2:'#dfd5c2',ink:'#112631',coal:'#081116',slate:'#38515d',mint:'#43cbb1',rust:'#d56c4b',gold:'#ddb15f',white:'#fbf8f1'};
const clamp={extrapolateLeft:'clamp' as const,extrapolateRight:'clamp' as const};

export type MaterialBeat={beat_id:string;start_seconds:number;end_seconds:number;duration_seconds:number;layout:string;family:string;purpose:string;asset?:string|null;label:string;detail:string;focus?:string};
export type PositioningScene={scene_id:string;duration_seconds:number;narration:string;caption:string;visual_kind:string;source:string;headline:string;dek?:string;material_plan:MaterialBeat[]};
export type PositioningProps={proofId:string;creativeSourceSha256:string;captionsVisible:boolean;variant:'short'|'longform';scenes:PositioningScene[];audioFile:string};

const src=(name:string)=>staticFile(`assets/${name}`);
const fmt=(value:number)=>`${value>0?'+':'−'}${(Math.abs(value)/1_000_000).toFixed(2)}m`;
const positions=[{label:'2Y',asset:1680389,lever:-1359521},{label:'5Y',asset:2883977,lever:-2147744},{label:'10Y',asset:2554411,lever:-2163714}];

const Grain:React.FC=()=> <AbsoluteFill style={{opacity:.11,backgroundImage:'radial-gradient(circle at 15% 20%,rgba(255,255,255,.8) 0 1px,transparent 1.5px),radial-gradient(circle at 70% 80%,rgba(8,17,22,.55) 0 1px,transparent 1.6px)',backgroundSize:'23px 29px,31px 27px',mixBlendMode:'soft-light'}}/>;
const Brand:React.FC<{dark?:boolean;portrait:boolean}>=({dark=true,portrait})=><div style={{position:'absolute',zIndex:80,top:portrait?45:32,right:portrait?46:58,color:dark?C.white:C.ink,fontSize:portrait?18:15,fontWeight:900,letterSpacing:2.2}}>CAPITAL <span style={{color:C.mint}}>CHRONICLE</span></div>;
const SourceLine:React.FC<{children:React.ReactNode;dark?:boolean;portrait:boolean}>=({children,dark=true,portrait})=><div style={{position:'absolute',zIndex:90,left:portrait?44:58,right:portrait?44:58,bottom:portrait?36:24,color:dark?'rgba(255,255,255,.92)':C.slate,fontSize:portrait?20:16,lineHeight:1.22,fontWeight:650,borderTop:`1px solid ${dark?'rgba(255,255,255,.3)':'rgba(17,38,49,.25)'}`,paddingTop:10}}>{children}</div>;
const ChapterSlug:React.FC<{scene:PositioningScene;portrait:boolean;dark?:boolean}>=({scene,portrait,dark=true})=><div style={{position:'absolute',zIndex:70,left:portrait?44:58,top:portrait?43:34,color:dark?C.gold:C.rust,fontSize:portrait?18:15,fontWeight:900,letterSpacing:2.4,textTransform:'uppercase'}}>{scene.scene_id.replace(/_/g,' ')}</div>;

const BeatTitle:React.FC<{beat:MaterialBeat;portrait:boolean;dark?:boolean;align?:'left'|'center'}>=({beat,portrait,dark=true,align='left'})=><div style={{textAlign:align,maxWidth:portrait?'92%':'78%'}}><div style={{fontSize:portrait?55:54,lineHeight:.96,letterSpacing:'-.035em',fontWeight:950,color:dark?C.white:C.ink,textTransform:'uppercase'}}>{beat.label}</div><div style={{fontSize:portrait?27:24,lineHeight:1.25,fontWeight:680,color:dark?'rgba(255,255,255,.8)':C.slate,marginTop:14}}>{beat.detail}</div></div>;

const PhotoFull:React.FC<{beat:MaterialBeat;portrait:boolean;progress:number}>=({beat,portrait,progress})=>{
  const objectPosition=beat.focus==='left'?'28% center':beat.focus==='right'?'72% center':'center';
  return <AbsoluteFill style={{background:C.coal}}><Img src={src(beat.asset!)} style={{width:'100%',height:'100%',objectFit:'cover',objectPosition,transform:`scale(${1.04+progress*.05})`,filter:'saturate(.82) contrast(1.04)'}}/><AbsoluteFill style={{background:portrait?'linear-gradient(180deg,rgba(8,17,22,.04) 22%,rgba(8,17,22,.9) 78%)':'linear-gradient(90deg,rgba(8,17,22,.9) 0%,rgba(8,17,22,.55) 44%,rgba(8,17,22,.08) 76%)'}}/><div style={{position:'absolute',zIndex:5,left:portrait?50:74,right:portrait?50:'auto',bottom:portrait?180:130,width:portrait?'auto':800}}><BeatTitle beat={beat} portrait={portrait}/></div></AbsoluteFill>;
};

const Document:React.FC<{beat:MaterialBeat;portrait:boolean;progress:number;figure?:boolean}>=({beat,portrait,progress,figure=false})=>{
  const crop=beat.layout.endsWith('_crop'); const objectPosition=beat.focus==='left'?'left center':beat.focus==='right'?'right center':'center';
  const dark=figure?C.coal:'#cfc3ad';
  return <AbsoluteFill style={{background:dark}}><div style={{position:'absolute',left:portrait?32:80,right:portrait?32:80,top:portrait?120:86,bottom:portrait?430:240,background:C.white,boxShadow:'0 30px 70px rgba(0,0,0,.32)',overflow:'hidden',borderRadius:portrait?7:4}}><Img src={src(beat.asset!)} style={{width:'100%',height:'100%',objectFit:crop?'cover':'contain',objectPosition,transform:`scale(${crop?1.04+progress*.055:1+progress*.012})`,background:C.white}}/></div><div style={{position:'absolute',zIndex:6,left:portrait?46:62,right:portrait?46:62,bottom:portrait?150:102,display:'flex',alignItems:'flex-end',justifyContent:'space-between',gap:30}}><BeatTitle beat={beat} portrait={portrait} dark={figure}/><div style={{fontSize:portrait?18:15,color:figure?C.gold:C.rust,fontWeight:900,letterSpacing:1.5,whiteSpace:'nowrap'}}>SOURCE MATERIAL · {crop?'DETAIL':'FULL VIEW'}</div></div></AbsoluteFill>;
};

const PositionChart:React.FC<{beat:MaterialBeat;portrait:boolean;local:number}>=({beat,portrait,local})=>{
  const grow=interpolate(local,[4,32],[0,1],clamp); const w=portrait?900:1320;
  return <AbsoluteFill style={{background:C.paper,color:C.ink,padding:portrait?'155px 62px 165px':'120px 95px 110px'}}><div style={{height:'100%',display:'flex',flexDirection:'column',justifyContent:'center'}}><BeatTitle beat={beat} portrait={portrait} dark={false}/><div style={{marginTop:portrait?75:46,width:w,maxWidth:'100%',display:'grid',gap:portrait?55:35}}>{positions.map((row,index)=>{const enter=spring({frame:local-index*7,fps:30,config:{damping:18,stiffness:130}});return <div key={row.label} style={{display:'grid',gridTemplateColumns:portrait?'90px 1fr':'120px 1fr',alignItems:'center',gap:22,opacity:enter}}><div style={{fontSize:portrait?37:31,fontWeight:950}}>{row.label}</div><div style={{position:'relative',height:portrait?100:76,borderLeft:`2px solid ${C.slate}`}}><div style={{position:'absolute',left:'50%',top:0,height:portrait?40:31,width:`${grow*Math.abs(row.asset)/3_000_000*50}%`,background:C.mint}}><b style={{position:'absolute',left:12,top:portrait?4:2,fontSize:portrait?25:21}}>{fmt(row.asset)}</b></div><div style={{position:'absolute',right:'50%',bottom:0,height:portrait?40:31,width:`${grow*Math.abs(row.lever)/3_000_000*50}%`,background:C.rust}}><b style={{position:'absolute',right:12,top:portrait?4:2,color:C.white,fontSize:portrait?25:21}}>{fmt(row.lever)}</b></div></div></div>})}</div><div style={{display:'flex',gap:28,marginTop:portrait?50:32,fontSize:portrait?21:17,fontWeight:800}}><span style={{color:'#087d69'}}>■ ASSET MANAGER NET</span><span style={{color:C.rust}}>■ LEVERAGED FUND NET</span></div></div></AbsoluteFill>;
};

const WeeklyDelta:React.FC<{beat:MaterialBeat;portrait:boolean;local:number}>=({beat,portrait,local})=>{
  const five=beat.label.includes('5-YEAR'); const rows=five?[['ASSET MANAGER','−79,277','LONG TRIMMED'],['LEVERAGED FUND','+63,695','SHORT LESS NEGATIVE']]:[['ASSET MANAGER','−40,268','LONG TRIMMED'],['LEVERAGED FUND','+67,956','SHORT LESS NEGATIVE']];
  return <AbsoluteFill style={{background:C.white,color:C.ink,padding:portrait?'165px 58px':'120px 100px'}}><BeatTitle beat={beat} portrait={portrait} dark={false}/><div style={{display:'grid',gridTemplateColumns:portrait?'1fr':'1fr 1fr',gap:24,marginTop:portrait?82:52}}>{rows.map((row,index)=>{const p=spring({frame:local-index*10,fps:30,config:{damping:17}});return <div key={row[0]} style={{background:index?C.coal:C.paper2,color:index?C.white:C.ink,padding:portrait?'42px 38px':'42px 44px',transform:`translateY(${(1-p)*28}px)`,opacity:p,borderLeft:`10px solid ${index?C.rust:C.mint}`}}><div style={{fontSize:portrait?23:20,fontWeight:900,letterSpacing:1.3}}>{row[0]}</div><div style={{fontSize:portrait?88:78,fontWeight:950,letterSpacing:'-.05em',marginTop:20}}>{row[1]}</div><div style={{fontSize:portrait?22:19,color:index?'#c2d0d6':C.slate,fontWeight:800}}>{row[2]}</div></div>})}</div></AbsoluteFill>;
};

const Mechanism:React.FC<{beat:MaterialBeat;portrait:boolean;local:number}>=({beat,portrait,local})=>{
  const duration=beat.label.includes('SYNTHETIC')?['CASH BUFFER','LONG FUTURE','DURATION NOW']:beat.label.includes('CONNECT')?['DEALER','REPO LENDER','CLEARING']:['REPO CASH','CASH TREASURY','SHORT FUTURE','CONVERGENCE'];
  return <AbsoluteFill style={{background:C.coal,color:C.white,padding:portrait?'165px 54px':'118px 82px'}}><BeatTitle beat={beat} portrait={portrait}/><div style={{display:'flex',flexDirection:portrait?'column':'row',gap:portrait?22:18,marginTop:portrait?74:54,alignItems:'stretch'}}>{duration.map((text,index)=>{const p=spring({frame:local-index*8,fps:30,config:{damping:18,stiffness:135}});return <React.Fragment key={text}><div style={{flex:1,minHeight:portrait?140:180,display:'flex',alignItems:'center',justifyContent:'center',textAlign:'center',padding:20,background:index%2?C.paper:C.mint,color:C.ink,fontSize:portrait?32:29,fontWeight:950,opacity:p,transform:`translate${portrait?'X':'Y'}(${(1-p)*24}px)`}}>{text}</div>{index<duration.length-1&&<div style={{alignSelf:'center',fontSize:portrait?34:30,color:C.gold}}>{portrait?'↓':'→'}</div>}</React.Fragment>})}</div></AbsoluteFill>;
};

const Boundary:React.FC<{beat:MaterialBeat;portrait:boolean;local:number}>=({beat,portrait,local})=>{
  const p=spring({frame:local-5,fps:30,config:{damping:16,stiffness:120}});
  return <AbsoluteFill style={{background:C.rust,color:C.white,padding:portrait?'180px 62px':'130px 105px'}}><div style={{position:'absolute',fontSize:portrait?600:470,fontWeight:950,right:portrait?-30:80,top:portrait?420:170,opacity:.12,transform:`scale(${.8+.2*p})`}}>≠</div><div style={{position:'relative',height:'100%',display:'flex',flexDirection:'column',justifyContent:'center'}}><div style={{fontSize:portrait?24:20,fontWeight:950,letterSpacing:3,color:C.coal}}>EVIDENCE BOUNDARY</div><div style={{fontSize:portrait?83:80,lineHeight:.93,fontWeight:950,letterSpacing:'-.055em',maxWidth:portrait?'95%':'78%',marginTop:28}}>{beat.label}</div><div style={{height:8,width:`${p*72}%`,background:C.gold,marginTop:38}}/><div style={{fontSize:portrait?34:31,lineHeight:1.25,fontWeight:750,maxWidth:portrait?'92%':'70%',marginTop:30}}>{beat.detail}</div></div></AbsoluteFill>;
};

const SourceClock:React.FC<{beat:MaterialBeat;portrait:boolean;local:number}>=({beat,portrait,local})=>{
  const nodes=[['TUE 11','POSITIONS MEASURED'],['FRI 14','REPORT PUBLISHED'],['AFTER','MARKET KEEPS MOVING']];
  return <AbsoluteFill style={{background:C.paper,color:C.ink,padding:portrait?'170px 56px':'125px 90px'}}><BeatTitle beat={beat} portrait={portrait} dark={false}/><div style={{display:'flex',flexDirection:portrait?'column':'row',gap:portrait?30:20,marginTop:portrait?85:60}}>{nodes.map((node,index)=>{const p=spring({frame:local-index*10,fps:30,config:{damping:18}});return <div key={node[0]} style={{flex:1,background:index===1?C.gold:C.coal,color:index===1?C.ink:C.white,padding:portrait?'38px 40px':'48px 38px',opacity:p,transform:`translateY(${(1-p)*24}px)`}}><div style={{fontSize:portrait?65:60,fontWeight:950}}>{node[0]}</div><div style={{fontSize:portrait?24:20,fontWeight:850,marginTop:12}}>{node[1]}</div></div>})}</div></AbsoluteFill>;
};

const StressChain:React.FC<{beat:MaterialBeat;portrait:boolean;local:number}>=({beat,portrait,local})=>{
  const nodes=['MARGIN ↑','REPO TIGHTENS','POSITIONS UNWIND','DEPTH FALLS'];
  return <AbsoluteFill style={{background:C.white,color:C.ink,padding:portrait?'165px 54px':'118px 82px'}}><BeatTitle beat={beat} portrait={portrait} dark={false}/><div style={{display:'grid',gridTemplateColumns:portrait?'1fr':'repeat(4,1fr)',gap:portrait?18:14,marginTop:portrait?70:55}}>{nodes.map((node,index)=>{const p=spring({frame:local-index*8,fps:30,config:{damping:17}});return <div key={node} style={{height:portrait?125:210,display:'flex',alignItems:'center',justifyContent:'center',textAlign:'center',background:index>1?C.rust:index===1?C.gold:C.coal,color:index===1?C.ink:C.white,fontSize:portrait?31:28,fontWeight:950,opacity:p,transform:`scale(${.9+.1*p})`}}>{node}</div>})}</div></AbsoluteFill>;
};

const Monitoring:React.FC<{beat:MaterialBeat;portrait:boolean;local:number}>=({beat,portrait,local})=>{
  const rows=['POSITIONING','FINANCING','CASH–FUTURES GAP','MARKET LIQUIDITY'];
  return <AbsoluteFill style={{background:C.coal,color:C.white,padding:portrait?'165px 56px':'118px 90px'}}><BeatTitle beat={beat} portrait={portrait}/><div style={{marginTop:portrait?70:45,display:'grid',gap:12}}>{rows.map((row,index)=>{const p=spring({frame:local-index*7,fps:30,config:{damping:18}});return <div key={row} style={{height:portrait?105:78,display:'grid',gridTemplateColumns:'90px 1fr 80px',alignItems:'center',background:index%2?'#142832':'#102028',borderLeft:`9px solid ${index<2?C.mint:C.gold}`,padding:'0 25px',opacity:p}}><b style={{fontSize:portrait?27:23,color:C.gold}}>0{index+1}</b><b style={{fontSize:portrait?28:24}}>{row}</b><span style={{fontSize:portrait?24:20,color:C.mint,textAlign:'right'}}>CHECK</span></div>})}</div></AbsoluteFill>;
};

const Montage:React.FC<{beat:MaterialBeat;portrait:boolean;local:number}>=({beat,portrait,local})=>{
  const words=['SOURCE','MECHANISM','BOUNDARY','TEST'];
  return <AbsoluteFill style={{background:C.paper,color:C.ink}}><div style={{display:'grid',gridTemplateColumns:portrait?'1fr 1fr':'repeat(4,1fr)',height:'100%'}}>{words.map((word,index)=>{const p=spring({frame:local-index*6,fps:30,config:{damping:18}});const colors=[C.coal,C.mint,C.gold,C.rust];return <div key={word} style={{background:colors[index],color:index===1||index===2?C.ink:C.white,display:'flex',alignItems:'center',justifyContent:'center',writingMode:portrait?'horizontal-tb':'vertical-rl',transform:portrait?`scale(${.95+.05*p})`:`rotate(180deg) scale(${.95+.05*p})`,fontSize:portrait?38:50,fontWeight:950,letterSpacing:3,opacity:p}}>{word}</div>})}</div><div style={{position:'absolute',left:portrait?48:90,right:portrait?48:90,bottom:portrait?150:105,background:C.white,padding:portrait?'34px 32px':'28px 38px',boxShadow:'0 20px 60px rgba(0,0,0,.25)'}}><BeatTitle beat={beat} portrait={portrait} dark={false}/></div></AbsoluteFill>;
};

const Material:React.FC<{scene:PositioningScene;beat:MaterialBeat;portrait:boolean;local:number;progress:number}>=({beat,portrait,local,progress})=>{
  if(beat.layout==='photo_full') return <PhotoFull beat={beat} portrait={portrait} progress={progress}/>;
  if(beat.layout.startsWith('document_')) return <Document beat={beat} portrait={portrait} progress={progress}/>;
  if(beat.layout.startsWith('figure_')) return <Document beat={beat} portrait={portrait} progress={progress} figure/>;
  if(beat.layout==='position_chart') return <PositionChart beat={beat} portrait={portrait} local={local}/>;
  if(beat.layout==='weekly_delta') return <WeeklyDelta beat={beat} portrait={portrait} local={local}/>;
  if(beat.layout==='mechanism') return <Mechanism beat={beat} portrait={portrait} local={local}/>;
  if(beat.layout==='boundary') return <Boundary beat={beat} portrait={portrait} local={local}/>;
  if(beat.layout==='source_clock') return <SourceClock beat={beat} portrait={portrait} local={local}/>;
  if(beat.layout==='stress_chain') return <StressChain beat={beat} portrait={portrait} local={local}/>;
  if(beat.layout==='monitoring') return <Monitoring beat={beat} portrait={portrait} local={local}/>;
  return <Montage beat={beat} portrait={portrait} local={local}/>;
};

const Scene:React.FC<{scene:PositioningScene;portrait:boolean;caption:boolean}>=({scene,portrait,caption})=>{
  const frame=useCurrentFrame(); const second=frame/30; const beats=scene.material_plan;
  const beat=beats.find(row=>second>=row.start_seconds&&second<row.end_seconds)??beats[beats.length-1];
  const local=Math.max(0,frame-Math.round(beat.start_seconds*30)); const duration=Math.max(1,Math.round(beat.duration_seconds*30));
  const progress=interpolate(local,[0,duration],[0,1],clamp); const edge=interpolate(local,[0,5],[.88,1],clamp);
  const dark=!['document_full','document_crop','position_chart','weekly_delta','source_clock','stress_chain','montage'].includes(beat.layout);
  return <AbsoluteFill style={{opacity:edge,background:C.coal}}><Material scene={scene} beat={beat} portrait={portrait} local={local} progress={progress}/><Grain/><ChapterSlug scene={scene} portrait={portrait} dark={dark}/><Brand portrait={portrait} dark={dark}/><SourceLine portrait={portrait} dark={dark}>{scene.source}</SourceLine>{caption&&<div style={{position:'absolute',zIndex:120,left:portrait?48:280,right:portrait?48:280,bottom:portrait?92:55,background:'rgba(8,17,22,.9)',color:C.white,padding:'13px 20px',fontSize:portrait?29:27,fontWeight:800,textAlign:'center'}}>{scene.caption}</div>}</AbsoluteFill>;
};

const PositioningVideo:React.FC<PositioningProps>=(props)=>{let cursor=0;const portrait=props.variant==='short';return <AbsoluteFill style={{background:C.coal}}><Audio src={staticFile(props.audioFile)}/>{props.scenes.map(scene=>{const from=Math.round(cursor*30);const duration=Math.max(1,Math.round(scene.duration_seconds*30));cursor+=scene.duration_seconds;return <Sequence key={scene.scene_id} from={from} durationInFrames={duration} premountFor={30}><Scene scene={scene} portrait={portrait} caption={props.captionsVisible}/></Sequence>})}</AbsoluteFill>};

export const TreasuryPositioningShort:React.FC<PositioningProps>=(props)=><PositioningVideo {...props} variant="short"/>;
export const TreasuryPositioningLongform:React.FC<PositioningProps>=(props)=><PositioningVideo {...props} variant="longform"/>;
