/* CODEX_VIEWER_FACING_AUTHORSHIP: story-specific CFTC Treasury positioning edit. */
import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, spring, staticFile, useCurrentFrame} from 'remotion';
import {BRAND, Brand, Canvas, Enter, Eyebrow, Grid, Pill, Source, Title, clamp} from '../lowLevel';

export type PositioningScene={scene_id:string;duration_seconds:number;narration:string;caption:string;visual_kind:string;source:string;headline:string;dek?:string};
export type PositioningProps={proofId:string;creativeSourceSha256:string;captionsVisible:boolean;variant:'short'|'longform';scenes:PositioningScene[];audioFile:string};

const fmt=(value:number)=>`${value>0?'+':''}${(value/1_000_000).toFixed(2)}m`;
const positions=[
  {label:'2-year',asset:1680389,lever:-1359521},
  {label:'5-year',asset:2883977,lever:-2147744},
  {label:'10-year',asset:2554411,lever:-2163714},
];

const PositionBars:React.FC<{portrait:boolean}> = ({portrait}) => {
  const frame=useCurrentFrame(); const p=interpolate(frame,[8,52],[0,1],clamp);
  const width=portrait?800:1280;
  return <div style={{display:'grid',gap:portrait?34:25,width}}>{positions.map((row,i)=><div key={row.label} style={{display:'grid',gridTemplateColumns:portrait?'120px 1fr':'160px 1fr',gap:20,alignItems:'center',opacity:interpolate(frame,[i*8,i*8+18],[0,1],clamp)}}><div style={{fontSize:portrait?30:28,fontWeight:900}}>{row.label}</div><div><div style={{height:portrait?37:31,width:`${p*Math.abs(row.asset)/3_000_000*50}%`,marginLeft:'50%',background:BRAND.teal,borderRadius:'0 8px 8px 0',position:'relative'}}><span style={{position:'absolute',left:12,top:3,fontSize:portrait?23:20,fontWeight:900,color:BRAND.navy}}>{fmt(row.asset)}</span></div><div style={{height:portrait?37:31,width:`${p*Math.abs(row.lever)/3_000_000*50}%`,marginLeft:`${50-p*Math.abs(row.lever)/3_000_000*50}%`,background:BRAND.copper,borderRadius:'8px 0 0 8px',position:'relative'}}><span style={{position:'absolute',right:12,top:3,fontSize:portrait?23:20,fontWeight:900,color:BRAND.navy}}>{fmt(row.lever)}</span></div></div></div>)}</div>;
};

const RepoChain:React.FC<{portrait:boolean}> = ({portrait}) => {
  const frame=useCurrentFrame(); const labels=['Borrow cash in repo','Buy a cash Treasury','Short a Treasury future','Harvest a small price gap'];
  return <div style={{display:'flex',flexDirection:portrait?'column':'row',gap:18,alignItems:'stretch',marginTop:40}}>{labels.map((label,i)=>{const p=spring({frame:frame-i*13,fps:30,config:{damping:18,stiffness:120}});return <React.Fragment key={label}><div style={{flex:1,padding:portrait?'25px 28px':'32px 24px',border:`2px solid ${i===3?BRAND.copper:BRAND.teal}`,background:'rgba(6,18,28,.92)',borderRadius:18,fontSize:portrait?30:25,fontWeight:850,opacity:p,transform:`translateY(${(1-p)*24}px)`}}>{label}</div>{i<labels.length-1&&<div style={{fontSize:32,alignSelf:'center',color:BRAND.muted}}>{portrait?'↓':'→'}</div>}</React.Fragment>})}</div>;
};

const FlowChain:React.FC<{portrait:boolean;labels:string[];tone?:'risk'|'neutral'}> = ({portrait,labels,tone='neutral'}) => {const frame=useCurrentFrame();return <div style={{display:'flex',flexDirection:portrait?'column':'row',gap:18,alignItems:'stretch',marginTop:40}}>{labels.map((label,i)=>{const p=spring({frame:frame-i*13,fps:30,config:{damping:18,stiffness:120}});const color=tone==='risk'&&i>1?BRAND.red:BRAND.teal;return <React.Fragment key={label}><div style={{flex:1,padding:portrait?'25px 28px':'32px 24px',border:`2px solid ${color}`,background:'rgba(6,18,28,.92)',borderRadius:18,fontSize:portrait?30:25,fontWeight:850,opacity:p,transform:`translateY(${(1-p)*24}px)`}}>{label}</div>{i<labels.length-1&&<div style={{fontSize:32,alignSelf:'center',color:BRAND.muted}}>{portrait?'↓':'→'}</div>}</React.Fragment>})}</div>};

const DocumentRow:React.FC<{portrait:boolean}> = ({portrait}) => <div style={{border:'2px solid rgba(168,184,196,.42)',borderRadius:20,overflow:'hidden',marginTop:portrait?36:28,background:'#f5f0e6',color:BRAND.navy,width:portrait?'100%':'86%'}}><div style={{padding:'16px 22px',background:'#d8e1e4',fontSize:portrait?22:18,fontWeight:900}}>CFTC TRADERS IN FINANCIAL FUTURES · 2026-08-11</div><div style={{display:'grid',gridTemplateColumns:'1.2fr repeat(3,1fr)',padding:portrait?'22px 20px':'24px 28px',gap:portrait?14:24,fontSize:portrait?25:23,lineHeight:1.35}}><b>Contract</b><b>Open interest</b><b>Asset manager net</b><b>Leveraged fund net</b>{positions.map((row,i)=><React.Fragment key={row.label}><span>{row.label}</span><span>{['4,377,812','6,442,950','5,458,890'][i]}</span><b style={{color:'#087a67'}}>{fmt(row.asset)}</b><b style={{color:'#a45d08'}}>{fmt(row.lever)}</b></React.Fragment>)}</div></div>;

const Timeline:React.FC<{portrait:boolean}> = ({portrait}) => {const frame=useCurrentFrame();return <div style={{display:'flex',flexDirection:portrait?'column':'row',gap:20,marginTop:45}}>{['Tuesday: positions measured','Friday: report released','Afterward: market can move'].map((text,i)=><div key={text} style={{flex:1,padding:28,borderTop:`7px solid ${i===1?BRAND.copper:BRAND.teal}`,background:'rgba(245,240,230,.08)',fontSize:portrait?31:27,fontWeight:850,opacity:interpolate(frame,[i*18,i*18+20],[0,1],clamp)}}>{text}</div>)}</div>};

const Tests:React.FC<{portrait:boolean}> = ({portrait}) => <div style={{display:'grid',gridTemplateColumns:portrait?'1fr':'1fr 1fr',gap:22,marginTop:36}}><div style={{padding:30,border:`2px solid ${BRAND.teal}`,borderRadius:20}}><Pill>CONFIRM</Pill><div style={{fontSize:portrait?30:26,lineHeight:1.35,marginTop:18}}>Persistent short futures, elevated repo borrowing, and stable cash–futures gaps.</div></div><div style={{padding:30,border:`2px solid ${BRAND.red}`,borderRadius:20}}><Pill color={BRAND.red}>CHALLENGE</Pill><div style={{fontSize:portrait?30:26,lineHeight:1.35,marginTop:18}}>Shorts unwind without repo stress, or the positioning reflects unrelated hedges.</div></div></div>;

const Scene:React.FC<{scene:PositioningScene;portrait:boolean;caption:boolean}> = ({scene,portrait,caption}) => {
  const frame=useCurrentFrame(); const pulse=interpolate(frame,[0,18,60],[.7,1,.82],clamp);
  let visual:React.ReactNode;
  if(scene.visual_kind==='positions'||scene.visual_kind==='history') visual=<PositionBars portrait={portrait}/>;
  else if(scene.visual_kind==='document') visual=<DocumentRow portrait={portrait}/>;
  else if(scene.scene_id==='L07_ASSET_MANAGER_JOB') visual=<FlowChain portrait={portrait} labels={['Keep cash available','Add futures exposure','Receive duration quickly']}/>;
  else if(scene.scene_id==='L13_STRESS_CHAIN'||scene.scene_id==='S07_STRESS_TEST') visual=<FlowChain portrait={portrait} tone="risk" labels={['Margin calls rise','Repo terms tighten','Positions unwind','Market depth falls']}/>;
  else if(scene.visual_kind==='mechanism'||scene.visual_kind==='repo') visual=<RepoChain portrait={portrait}/>;
  else if(scene.visual_kind==='timing') visual=<Timeline portrait={portrait}/>;
  else if(scene.visual_kind==='test'||scene.visual_kind==='risk') visual=<Tests portrait={portrait}/>;
  else visual=<div style={{marginTop:portrait?80:55,display:'flex',alignItems:'baseline',gap:20}}><div style={{fontSize:portrait?145:135,fontWeight:950,color:BRAND.teal,transform:`scale(${pulse})`}}>2.88m</div><div style={{fontSize:portrait?34:30,color:BRAND.muted,maxWidth:portrait?470:600}}>net long five-year Treasury futures contracts held by asset managers</div></div>;
  return <Canvas portrait={portrait}><Grid/><Brand portrait={portrait}/><div style={{position:'relative',zIndex:3,height:'100%',display:'flex',flexDirection:'column',justifyContent:'center'}}><Enter><Eyebrow portrait={portrait}>{scene.scene_id.replace(/_/g,' ')}</Eyebrow><Title size={portrait?66:58} maxWidth={portrait?'100%':'85%'} style={{marginTop:14}}>{scene.headline}</Title>{scene.dek&&<div style={{fontSize:portrait?29:26,color:BRAND.muted,lineHeight:1.35,marginTop:18,maxWidth:portrait?'100%':'80%'}}>{scene.dek}</div>}</Enter><div style={{marginTop:portrait?28:12}}>{visual}</div></div><Source portrait={portrait}>{scene.source}</Source>{caption&&<div style={{position:'absolute',zIndex:100,left:portrait?70:280,right:portrait?70:280,bottom:portrait?125:65,padding:'14px 22px',borderRadius:12,background:'rgba(2,8,13,.88)',fontSize:portrait?30:28,fontWeight:800,textAlign:'center'}}>{scene.caption}</div>}</Canvas>;
};

const PositioningVideo:React.FC<PositioningProps> = (props) => {let cursor=0;const portrait=props.variant==='short';return <AbsoluteFill><Audio src={staticFile(props.audioFile)}/>{props.scenes.map(scene=>{const from=Math.round(cursor*30);const duration=Math.max(1,Math.round(scene.duration_seconds*30));cursor+=scene.duration_seconds;return <Sequence key={scene.scene_id} from={from} durationInFrames={duration} premountFor={30}><Scene scene={scene} portrait={portrait} caption={props.captionsVisible}/></Sequence>})}</AbsoluteFill>};

export const TreasuryPositioningShort:React.FC<PositioningProps>=(props)=><PositioningVideo {...props} variant="short"/>;
export const TreasuryPositioningLongform:React.FC<PositioningProps>=(props)=><PositioningVideo {...props} variant="longform"/>;
