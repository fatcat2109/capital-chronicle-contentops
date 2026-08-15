/* CODEX_VIEWER_FACING_AUTHORSHIP: material-rich editorial repair of the frozen Treasury story. */
import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame} from 'remotion';

const C={paper:'#f2ede2',paper2:'#dfd5c2',ink:'#112631',coal:'#081116',slate:'#38515d',mint:'#43cbb1',rust:'#d56c4b',gold:'#ddb15f',white:'#fbf8f1'};
const clamp={extrapolateLeft:'clamp' as const,extrapolateRight:'clamp' as const};

export type MaterialBeat={beat_id:string;start_seconds:number;end_seconds:number;duration_seconds:number;layout:string;family:string;source_material_family:string;presentation_grammar:string;purpose:string;asset?:string|null;label:string;detail:string;focus?:string;evidence_object_class:string;motion_policy:'STATIC_FULL_CONTEXT'|'PHOTO_EDITORIAL_REFRAME'|'NATIVE_GOVERNED_MOTION'|'SEMANTIC_COMPONENT_MOTION'|'STATIC_EDITORIAL_FRAME';readability_hold:boolean;boundary_authority:string};
export type WithinStateAction={action_id:string;semantic_beat_id:string;at_seconds:number;action:string;emphasis:string;utility:string};
export type VisualState={visual_state_id:string;scene_id:string;start_seconds:number;end_seconds:number;duration_seconds:number;semantic_beat_ids:string[];anchor_beat_id:string;display_layout:string;context_key:string;information_density:string;ingestion_rationale:string;progressive_disclosure:boolean;low_information_standalone_card:boolean;within_state_actions:WithinStateAction[];transition_in_id:string;stagnation_review:string};
export type TransitionEvent={transition_id:string;scene_id:string;to_visual_state_id:string;from_visual_state_id?:string|null;event_type:'chapter_entry'|'full_screen_context_reset';at_seconds:number;earned_by:string;new_context:string};
export type GovernedPosition={label:'2Y'|'5Y'|'10Y';open_interest:number;asset_net:number;lever_net:number;asset_net_weekly_change:number;lever_net_weekly_change:number;row_sha256:string};
export type PositioningScene={scene_id:string;duration_seconds:number;narration:string;caption:string;visual_kind:string;source:string;headline:string;dek?:string;material_plan:MaterialBeat[];visual_state_plan:VisualState[];transition_events:TransitionEvent[]};
export type PositioningProps={proofId:string;creativeSourceSha256:string;captionsVisible:boolean;variant:'short'|'longform';scenes:PositioningScene[];audioFile:string;governedPositions:GovernedPosition[]};

const src=(name:string)=>staticFile(`assets/${name}`);
const fmt=(value:number)=>`${value>0?'+':'−'}${(Math.abs(value)/1_000_000).toFixed(2)}m`;

const Grain:React.FC=()=> <AbsoluteFill style={{opacity:.11,backgroundImage:'radial-gradient(circle at 15% 20%,rgba(255,255,255,.8) 0 1px,transparent 1.5px),radial-gradient(circle at 70% 80%,rgba(8,17,22,.55) 0 1px,transparent 1.6px)',backgroundSize:'23px 29px,31px 27px',mixBlendMode:'soft-light'}}/>;
const Brand:React.FC<{dark?:boolean;portrait:boolean}>=({dark=true,portrait})=><div style={{position:'absolute',zIndex:80,top:portrait?45:32,right:portrait?46:58,color:dark?C.white:C.ink,fontSize:portrait?18:15,fontWeight:900,letterSpacing:2.2}}>CAPITAL <span style={{color:C.mint}}>CHRONICLE</span></div>;
const SourceLine:React.FC<{children:React.ReactNode;dark?:boolean;portrait:boolean}>=({children,dark=true,portrait})=><div style={{position:'absolute',zIndex:90,left:portrait?44:58,right:portrait?44:58,bottom:portrait?36:24,color:dark?'rgba(255,255,255,.92)':C.slate,fontSize:portrait?20:16,lineHeight:1.22,fontWeight:650,borderTop:`1px solid ${dark?'rgba(255,255,255,.3)':'rgba(17,38,49,.25)'}`,paddingTop:10}}>{children}</div>;
const ChapterSlug:React.FC<{scene:PositioningScene;portrait:boolean;dark?:boolean}>=({scene,portrait,dark=true})=><div style={{position:'absolute',zIndex:70,left:portrait?44:58,top:portrait?43:34,maxWidth:portrait?'72%':'66%',color:dark?C.gold:C.rust,fontSize:portrait?18:15,fontWeight:900,letterSpacing:2.1,textTransform:'uppercase'}}>{scene.headline}</div>;

const BeatTitle:React.FC<{beat:MaterialBeat;portrait:boolean;dark?:boolean;align?:'left'|'center'}>=({beat,portrait,dark=true,align='left'})=><div style={{textAlign:align,maxWidth:portrait?'92%':'78%'}}><div style={{fontSize:portrait?55:54,lineHeight:.96,letterSpacing:'-.035em',fontWeight:950,color:dark?C.white:C.ink,textTransform:'uppercase'}}>{beat.label}</div><div style={{fontSize:portrait?27:24,lineHeight:1.25,fontWeight:680,color:dark?'rgba(255,255,255,.8)':C.slate,marginTop:14}}>{beat.detail}</div></div>;

const PhotoFull:React.FC<{beat:MaterialBeat;portrait:boolean;progress:number}>=({beat,portrait,progress})=>{
  const objectPosition=beat.focus==='left'?'28% center':beat.focus==='right'?'72% center':'center';
  return <AbsoluteFill style={{background:C.coal}}><Img src={src(beat.asset!)} style={{width:'100%',height:'100%',objectFit:'cover',objectPosition,transform:`scale(${1.04+progress*.05})`,filter:'saturate(.82) contrast(1.04)'}}/><AbsoluteFill style={{background:portrait?'linear-gradient(180deg,rgba(8,17,22,.04) 22%,rgba(8,17,22,.9) 78%)':'linear-gradient(90deg,rgba(8,17,22,.9) 0%,rgba(8,17,22,.55) 44%,rgba(8,17,22,.08) 76%)'}}/><div style={{position:'absolute',zIndex:5,left:portrait?50:74,right:portrait?50:'auto',bottom:portrait?180:130,width:portrait?'auto':800}}><BeatTitle beat={beat} portrait={portrait}/></div></AbsoluteFill>;
};

const Document:React.FC<{beat:MaterialBeat;portrait:boolean;progress:number;figure?:boolean}>=({beat,portrait,figure=false})=>{
  const dark=figure?C.coal:'#cfc3ad';
  return <AbsoluteFill style={{background:dark}}><div style={{position:'absolute',left:portrait?32:80,right:portrait?32:80,top:portrait?120:86,bottom:portrait?430:240,background:C.white,boxShadow:'0 30px 70px rgba(0,0,0,.32)',overflow:'hidden',borderRadius:portrait?7:4}}><Img src={src(beat.asset!)} style={{width:'100%',height:'100%',objectFit:'contain',objectPosition:'center',transform:'none',background:C.white}}/></div><div style={{position:'absolute',zIndex:6,left:portrait?46:62,right:portrait?46:62,bottom:portrait?150:102,display:'flex',alignItems:'flex-end',justifyContent:'space-between',gap:30}}><BeatTitle beat={beat} portrait={portrait} dark={figure}/><div style={{fontSize:portrait?18:15,color:figure?C.gold:C.rust,fontWeight:900,letterSpacing:1.5,whiteSpace:'nowrap'}}>OFFICIAL SOURCE · FULL VIEW</div></div></AbsoluteFill>;
};

const PositionChart:React.FC<{beat:MaterialBeat;portrait:boolean;local:number;positions:GovernedPosition[]}>=({beat,portrait,local,positions})=>{
  const grow=interpolate(local,[4,32],[0,1],clamp); const w=portrait?900:1320;
  return <AbsoluteFill style={{background:C.paper,color:C.ink,padding:portrait?'155px 62px 165px':'120px 95px 110px'}}><div style={{height:'100%',display:'flex',flexDirection:'column',justifyContent:'center'}}><BeatTitle beat={beat} portrait={portrait} dark={false}/><div style={{marginTop:portrait?75:46,width:w,maxWidth:'100%',display:'grid',gap:portrait?55:35}}>{positions.map((row,index)=>{const enter=spring({frame:local-index*7,fps:30,config:{damping:18,stiffness:130}});return <div key={row.label} style={{display:'grid',gridTemplateColumns:portrait?'90px 1fr':'120px 1fr',alignItems:'center',gap:22,opacity:enter}}><div style={{fontSize:portrait?37:31,fontWeight:950}}>{row.label}</div><div style={{position:'relative',height:portrait?100:76,borderLeft:`2px solid ${C.slate}`}}><div style={{position:'absolute',left:'50%',top:0,height:portrait?40:31,width:`${grow*Math.abs(row.asset_net)/3_000_000*50}%`,background:C.mint}}><b style={{position:'absolute',left:12,top:portrait?4:2,fontSize:portrait?25:21}}>{fmt(row.asset_net)}</b></div><div style={{position:'absolute',right:'50%',bottom:0,height:portrait?40:31,width:`${grow*Math.abs(row.lever_net)/3_000_000*50}%`,background:C.rust}}><b style={{position:'absolute',right:12,top:portrait?4:2,color:C.white,fontSize:portrait?25:21}}>{fmt(row.lever_net)}</b></div></div></div>})}</div><div style={{display:'flex',gap:28,marginTop:portrait?50:32,fontSize:portrait?21:17,fontWeight:800}}><span style={{color:'#087d69'}}>■ ASSET MANAGER NET</span><span style={{color:C.rust}}>■ LEVERAGED FUND NET</span></div></div></AbsoluteFill>;
};

const MaturityData:React.FC<{beat:MaterialBeat;anchorBeat:MaterialBeat;portrait:boolean;local:number;positions:GovernedPosition[]}>=({beat,anchorBeat,portrait,local,positions})=>{
  const row=positions.find(item=>anchorBeat.label.startsWith(item.label))??positions[1];
  const reveal=spring({frame:local,fps:30,config:{damping:19,stiffness:120}});
  const card=(title:string,value:string,color:string,index:number)=><div style={{background:C.white,borderTop:`10px solid ${color}`,padding:portrait?'34px 30px':'30px 34px',boxShadow:'0 16px 45px rgba(17,38,49,.11)',opacity:spring({frame:local-index*7,fps:30,config:{damping:18}})}}><div style={{fontSize:portrait?20:17,fontWeight:900,letterSpacing:1.5,color:C.slate}}>{title}</div><div style={{fontSize:portrait?62:54,fontWeight:950,letterSpacing:'-.045em',color:C.ink,marginTop:13}}>{value}</div></div>;
  return <AbsoluteFill style={{background:`linear-gradient(135deg,${C.paper} 0%,${C.paper2} 100%)`,color:C.ink,padding:portrait?'165px 58px 155px':'118px 92px 100px'}}><BeatTitle beat={beat} portrait={portrait} dark={false}/><div style={{display:'grid',gridTemplateColumns:portrait?'1fr':'1.15fr .85fr',gap:portrait?26:34,marginTop:portrait?58:42,alignItems:'stretch'}}><div style={{background:C.coal,color:C.white,padding:portrait?'42px 36px':'40px 44px',display:'flex',flexDirection:'column',justifyContent:'space-between',minHeight:portrait?270:300,transform:`translateY(${(1-reveal)*22}px)`,opacity:reveal}}><div style={{fontSize:portrait?22:18,fontWeight:900,letterSpacing:1.8,color:C.gold}}>CFTC · WEEKLY REPORT</div><div><div style={{fontSize:portrait?90:84,fontWeight:950,letterSpacing:'-.055em'}}>{row.label}</div><div style={{fontSize:portrait?25:21,color:'#c2d0d6',fontWeight:750}}>OPEN INTEREST · {row.open_interest.toLocaleString('en-US')}</div></div><div style={{fontSize:portrait?18:15,color:C.mint,fontWeight:850}}>POSITIONS AS OF 11 AUG 2026</div></div><div style={{display:'grid',gap:portrait?20:18}}>{card('ASSET MANAGER NET',row.asset_net.toLocaleString('en-US',{signDisplay:'always'}),C.mint,1)}{card('LEVERAGED FUND NET',row.lever_net.toLocaleString('en-US',{signDisplay:'always'}),C.rust,2)}</div></div></AbsoluteFill>;
};

const WeeklyDelta:React.FC<{beat:MaterialBeat;portrait:boolean;local:number;positions:GovernedPosition[]}>=({beat,portrait,local,positions})=>{
  const label=beat.label.includes('10-YEAR')?'10Y':'5Y'; const position=positions.find(row=>row.label===label)??positions[1];
  const signed=(value:number)=>value.toLocaleString('en-US',{signDisplay:'always'}).replace('-', '−');
  const rows=[["ASSET MANAGER",signed(position.asset_net_weekly_change),'LONG TRIMMED'],['LEVERAGED FUND',signed(position.lever_net_weekly_change),'SHORT LESS NEGATIVE']];
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

const Material:React.FC<{scene:PositioningScene;beat:MaterialBeat;anchorBeat:MaterialBeat;portrait:boolean;local:number;progress:number;positions:GovernedPosition[]}>=({beat,anchorBeat,portrait,local,progress,positions})=>{
  if(beat.layout==='photo_full') return <PhotoFull beat={beat} portrait={portrait} progress={progress}/>;
  if(beat.layout.startsWith('document_')) return <Document beat={beat} portrait={portrait} progress={progress}/>;
  if(beat.layout.startsWith('figure_')) return <Document beat={beat} portrait={portrait} progress={progress} figure/>;
  if(beat.layout==='position_chart') return <PositionChart beat={beat} portrait={portrait} local={local} positions={positions}/>;
  if(beat.layout==='maturity_data') return <MaturityData beat={beat} anchorBeat={anchorBeat} portrait={portrait} local={local} positions={positions}/>;
  if(beat.layout==='weekly_delta') return <WeeklyDelta beat={beat} portrait={portrait} local={local} positions={positions}/>;
  if(beat.layout==='mechanism') return <Mechanism beat={beat} portrait={portrait} local={local}/>;
  if(beat.layout==='boundary') return <Boundary beat={beat} portrait={portrait} local={local}/>;
  if(beat.layout==='source_clock') return <SourceClock beat={beat} portrait={portrait} local={local}/>;
  if(beat.layout==='stress_chain') return <StressChain beat={beat} portrait={portrait} local={local}/>;
  if(beat.layout==='monitoring') return <Monitoring beat={beat} portrait={portrait} local={local}/>;
  return <Montage beat={beat} portrait={portrait} local={local}/>;
};

const Scene:React.FC<{scene:PositioningScene;portrait:boolean;caption:boolean;positions:GovernedPosition[]}>=({scene,portrait,caption,positions})=>{
  const frame=useCurrentFrame(); const second=frame/30; const beats=scene.material_plan;
  const beat=beats.find(row=>second>=row.start_seconds&&second<row.end_seconds)??beats[beats.length-1];
  const state=scene.visual_state_plan.find(row=>second>=row.start_seconds&&second<row.end_seconds)??scene.visual_state_plan[scene.visual_state_plan.length-1];
  const anchor=beats.find(row=>row.beat_id===state.anchor_beat_id)??beat;
  const displayBeat={...beat,layout:state.display_layout,asset:anchor.asset,focus:anchor.focus,evidence_object_class:anchor.evidence_object_class,motion_policy:anchor.motion_policy};
  const stateLocal=Math.max(0,frame-Math.round(state.start_seconds*30)); const stateDuration=Math.max(1,Math.round(state.duration_seconds*30));
  const actionLocal=Math.max(0,frame-Math.round(beat.start_seconds*30));
  const progress=interpolate(stateLocal,[0,stateDuration],[0,1],clamp); const edge=interpolate(stateLocal,[0,5],[.88,1],clamp);
  const cue=spring({frame:actionLocal,fps:30,config:{damping:20,stiffness:150}});
  const dark=!['document_full','position_chart','maturity_data','weekly_delta','source_clock','stress_chain','montage'].includes(displayBeat.layout);
  return <AbsoluteFill style={{opacity:edge,background:C.coal}}><Material scene={scene} beat={displayBeat} anchorBeat={anchor} portrait={portrait} local={stateLocal} progress={progress} positions={positions}/><div style={{position:'absolute',zIndex:65,left:portrait?44:58,bottom:portrait?118:72,width:`${cue*84}px`,height:5,background:C.mint}}/><Grain/><ChapterSlug scene={scene} portrait={portrait} dark={dark}/><Brand portrait={portrait} dark={dark}/><SourceLine portrait={portrait} dark={dark}>{scene.source}</SourceLine>{caption&&<div style={{position:'absolute',zIndex:120,left:portrait?48:280,right:portrait?48:280,bottom:portrait?92:55,background:'rgba(8,17,22,.9)',color:C.white,padding:'13px 20px',fontSize:portrait?29:27,fontWeight:800,textAlign:'center'}}>{scene.caption}</div>}</AbsoluteFill>;
};

const PositioningVideo:React.FC<PositioningProps>=(props)=>{let cursor=0;const portrait=props.variant==='short';return <AbsoluteFill style={{background:C.coal}}><Audio src={staticFile(props.audioFile)}/>{props.scenes.map(scene=>{const from=Math.round(cursor*30);const duration=Math.max(1,Math.round(scene.duration_seconds*30));cursor+=scene.duration_seconds;return <Sequence key={scene.scene_id} from={from} durationInFrames={duration} premountFor={30}><Scene scene={scene} portrait={portrait} caption={props.captionsVisible} positions={props.governedPositions}/></Sequence>})}</AbsoluteFill>};

export const TreasuryPositioningShort:React.FC<PositioningProps>=(props)=><PositioningVideo {...props} variant="short"/>;
export const TreasuryPositioningLongform:React.FC<PositioningProps>=(props)=><PositioningVideo {...props} variant="longform"/>;
