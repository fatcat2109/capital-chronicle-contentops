// CODEX_VIEWER_FACING_AUTHORSHIP: story-specific editorial composition.
import React from 'react';
import {AbsoluteFill, Img, interpolate, Sequence, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {BRAND, Brand, Canvas, clamp, Enter, Eyebrow, Grid, Pill, Scrim, Source, Title, YieldCurve, asset} from '../lowLevel';

type ProofProps={proofId:string;creativeSourceSha256:string;captionsVisible:boolean};
export const SHORT_FRAMES=1860; // 62 seconds
export const MIDFORM_FRAMES=4500; // 150 seconds

const TREASURY_A=asset('treasury-highsmith-12807.jpg');
const TREASURY_B=asset('treasury-highsmith-16870.jpg');
const FED_ROOM=asset('fed-boardroom-2019.jpg');
const HOUSE=asset('housing-modern-04230.jpg');
const CAPITOL_DUSK=asset('capitol-dusk-12505.jpg');
const CAPITOL_FRONT=asset('capitol-front-12945.jpg');

const curve=[
  {label:'1M',value:3.75,previous:3.72},{label:'3M',value:3.74,previous:3.70},
  {label:'6M',value:3.81,previous:3.76},{label:'1Y',value:3.97,previous:3.91},
  {label:'2Y',value:4.26,previous:4.21},{label:'5Y',value:4.40,previous:4.34},
  {label:'10Y',value:4.62,previous:4.56},{label:'20Y',value:4.97,previous:4.92},
  {label:'30Y',value:5.10,previous:5.06},
];
const mortgages=[{date:'JUL 02',value:6.43},{date:'JUL 09',value:6.49},{date:'JUL 16',value:6.55}];
const p=(f:number,a:number,b:number)=>interpolate(f,[a,b],[0,1],clamp);
const Watermark:React.FC<{portrait?:boolean}>=({portrait=false})=><><Brand portrait={portrait}/><div style={{position:'absolute',left:portrait?48:64,top:portrait?40:32,width:48,height:4,background:BRAND.teal,zIndex:70}}/></>;

const EditorialPhoto:React.FC<{src:string;position?:string;zoom?:number}>=({src,position='center',zoom=1.035})=>{const f=useCurrentFrame();const {durationInFrames}=useVideoConfig();const s=interpolate(f,[0,durationInFrames],[1,zoom],clamp);return <Img src={src} style={{width:'100%',height:'100%',objectFit:'cover',objectPosition:position,transform:`scale(${s})`}}/>};
const BigNumber:React.FC<{children:React.ReactNode;portrait?:boolean;accent?:string;compact?:boolean}>=({children,portrait=false,accent=BRAND.teal,compact=false})=><div style={{fontSize:compact?(portrait?88:90):(portrait?132:112),fontWeight:950,letterSpacing:compact?'-.045em':'-.07em',lineHeight:.9,color:accent}}>{children}</div>;
const Rule:React.FC<{width?:string;delay?:number}>=({width='100%',delay=0})=>{const f=useCurrentFrame();return <div style={{height:3,width,background:BRAND.teal,transform:`scaleX(${p(f,delay,delay+24)})`,transformOrigin:'left'}}/>};

const PhotoHook:React.FC<{portrait?:boolean;closing?:boolean}>=({portrait=false,closing=false})=>{const f=useCurrentFrame();const wipe=p(f,closing?10:44,closing?36:92);return <AbsoluteFill>
  <EditorialPhoto src={closing?TREASURY_B:TREASURY_A} position="center 46%"/><Scrim opacity={.67}/><Watermark portrait={portrait}/>
  <div style={{position:'absolute',left:portrait?54:90,right:portrait?54:490,top:portrait?270:190,zIndex:5}}>
    <Eyebrow portrait={portrait}>{closing?'The disciplined read':'U.S. rates • July 13, 2026'}</Eyebrow>
    <Title size={portrait?92:76} style={{marginTop:18}}>{closing?'The curve is a chain—not a verdict.':'The long bond crossed 5%.'}</Title>
    <div style={{marginTop:26,width:`${Math.max(7,wipe*100)}%`,overflow:'hidden',whiteSpace:'nowrap'}}><BigNumber portrait={portrait} accent={BRAND.copper} compact={closing}>{closing?'WATCH THE CHAIN':'5.10%'}</BigNumber></div>
    <Enter delay={closing?22:82}><div style={{fontSize:portrait?31:26,lineHeight:1.28,color:BRAND.muted,maxWidth:portrait?860:900,marginTop:28}}>{closing?'Curve breadth. Term premium. Mortgage transmission. Treasury demand.':'The shape matters more than the spectacle.'}</div></Enter>
  </div><Source portrait={portrait}>U.S. Treasury Daily Treasury Par Yield Curve Rates • observation, not a live quote</Source>
</AbsoluteFill>};

const CurveScene:React.FC<{portrait?:boolean;delta?:boolean}>=({portrait=false,delta=false})=>{const f=useCurrentFrame();const focus=p(f,delta?88:125,delta?145:190);return <Canvas portrait={portrait}><Grid/><Watermark portrait={portrait}/>
  <div style={{position:'relative',zIndex:3}}><Eyebrow portrait={portrait}>{delta?'One session • broad move':'Nine tenors • one curve'}</Eyebrow><Title size={portrait?66:54} style={{marginTop:14}}>{delta?'Not just the 30-year.':'Long rates lead the slope.'}</Title></div>
  <div style={{position:'absolute',left:portrait?54:105,top:portrait?500:255,transform:`translateY(${(1-focus)*10}px)`}}><YieldCurve points={curve} portrait={portrait} showPrevious active={delta?6:8}/></div>
  {delta?<div style={{position:'absolute',left:portrait?70:120,right:portrait?70:120,bottom:portrait?180:100,display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:16}}>{[['2Y','+5 bp'],['10Y','+6 bp'],['30Y','+4 bp']].map(([t,v],i)=><Enter key={t} delay={26+i*26}><div style={{padding:portrait?'21px 14px':'17px 22px',background:'rgba(12,30,42,.96)',borderTop:`4px solid ${i===1?BRAND.copper:BRAND.teal}`,textAlign:'center'}}><div style={{fontSize:portrait?24:20,color:BRAND.muted}}>{t}</div><div style={{fontSize:portrait?40:35,fontWeight:950}}>{v}</div></div></Enter>)}</div>:<Enter delay={170} style={{position:'absolute',right:portrait?72:110,bottom:portrait?182:108}}><Pill>2s10s = 36 bp • +1 bp</Pill></Enter>}
  <Source portrait={portrait}>U.S. Treasury • July 13 versus July 10 • Capital Chronicle same-date calculations</Source>
</Canvas>};

const EvidenceScene:React.FC<{portrait?:boolean}>=({portrait=false})=>{const f=useCurrentFrame();const row=p(f,55,100),extract=p(f,145,205);return <Canvas portrait={portrait} style={{background:'#e7e0d3',color:BRAND.navy}}><Watermark portrait={portrait}/>
  <div style={{position:'absolute',left:portrait?48:86,right:portrait?48:86,top:portrait?135:72,bottom:portrait?116:66,background:'#fffaf0',boxShadow:'0 24px 80px rgba(0,0,0,.3)',padding:portrait?'48px 40px':'34px 52px',overflow:'hidden'}}>
    <div style={{fontSize:portrait?19:16,fontWeight:900,letterSpacing:2,color:'#5e6d75'}}>PRIMARY DATA • EXACT OFFICIAL ROWS</div>
    <div style={{fontFamily:'Georgia,serif',fontSize:portrait?46:39,fontWeight:800,marginTop:16}}>Daily Treasury Par Yield Curve Rates</div>
    <div style={{fontSize:portrait?24:19,color:'#657178',marginTop:9}}>Observation dates: 07/10/2026 and 07/13/2026</div>
    <div style={{marginTop:portrait?46:28,display:'grid',gridTemplateColumns:'1.35fr repeat(3,1fr)',fontSize:portrait?27:22,borderTop:'2px solid #8c999f'}}>{['DATE','2-YEAR','10-YEAR','30-YEAR','07/10/2026','4.21','4.56','5.06','07/13/2026','4.26','4.62','5.10'].map((x,i)=><div key={i} style={{padding:portrait?'18px 8px':'14px 12px',borderBottom:'1px solid #b9c1c4',fontWeight:i>=8?900:650,background:i>=8?`rgba(66,213,184,${.24*row})`:'transparent',opacity:i>=8?row:1}}>{x}</div>)}</div>
    <div style={{marginTop:portrait?42:26,padding:portrait?'25px':'19px 24px',background:'#102936',color:BRAND.ink,transform:`translateY(${(1-extract)*18}px)`,opacity:extract}}><div style={{fontSize:portrait?21:18,color:BRAND.teal,fontWeight:900}}>CAPITAL CHRONICLE DERIVATION</div><div style={{fontSize:portrait?35:30,fontWeight:950,marginTop:8}}>4.62 − 4.26 = 36 basis points</div></div>
    <div style={{position:'absolute',left:portrait?40:52,bottom:portrait?28:20,fontSize:portrait?17:14,color:'#68747a'}}>V1 packet cc-publication-73ff151c3d3094741b6c • exact-source excerpt</div>
  </div><Source portrait={portrait} dark={false}>home.treasury.gov • official daily par-yield table and XML</Source>
</Canvas>};

const DecompositionScene:React.FC<{portrait?:boolean;wide?:boolean}>=({portrait=false,wide=false})=>{const f=useCurrentFrame();const split=p(f,52,95),risk=p(f,128,180);return <Canvas portrait={portrait}><AbsoluteFill style={{left:portrait?'36%':'52%',opacity:.36}}><EditorialPhoto src={FED_ROOM} position="center 46%"/></AbsoluteFill><Scrim opacity={.64}/><Watermark portrait={portrait}/>
  <div style={{position:'relative',zIndex:4,maxWidth:portrait?900:wide?1260:1050}}><Eyebrow portrait={portrait}>What a long yield contains</Eyebrow><Title size={portrait?63:53} style={{marginTop:14}}>Expected short rates <span style={{color:BRAND.muted}}>+</span> term premium.</Title>
  <div style={{marginTop:portrait?72:48,display:'grid',gridTemplateColumns:portrait?'1fr':'1fr 1fr',gap:20,maxWidth:portrait?900:1160}}><div style={{padding:portrait?'28px 26px':'26px 30px',border:`2px solid ${BRAND.teal}`,background:'rgba(5,18,28,.92)',opacity:split,transform:`translateX(${(1-split)*-35}px)`}}><div style={{fontSize:portrait?34:29,fontWeight:950,color:BRAND.teal}}>PATH EXPECTATIONS</div><div style={{fontSize:portrait?24:21,lineHeight:1.3,color:BRAND.muted,marginTop:12}}>The average short-rate path markets expect.</div></div><div style={{padding:portrait?'28px 26px':'26px 30px',border:`2px solid ${BRAND.copper}`,background:'rgba(5,18,28,.92)',opacity:risk,transform:`translateX(${(1-risk)*35}px)`}}><div style={{fontSize:portrait?34:29,fontWeight:950,color:BRAND.copper}}>TERM PREMIUM</div><div style={{fontSize:portrait?24:21,lineHeight:1.3,color:BRAND.muted,marginTop:12}}>Compensation for bearing duration risk. Estimated—not observed.</div></div></div>
  <Enter delay={205}><div style={{marginTop:25,fontSize:portrait?25:21,color:BRAND.muted}}>A higher 30-year yield is not a one-line forecast of the next Fed decision.</div></Enter></div>
  <Source portrait={portrait}>New York Fed ACM model • model output is not an official Federal Reserve estimate</Source>
</Canvas>};

const MortgageScene:React.FC<{portrait?:boolean;mechanism?:boolean}>=({portrait=false,mechanism=false})=>{const f=useCurrentFrame();const chart=p(f,55,100);return <Canvas portrait={portrait}><AbsoluteFill style={{right:portrait?'20%':'48%',opacity:.48}}><EditorialPhoto src={HOUSE} position="center 52%"/></AbsoluteFill><Scrim opacity={.62}/><Watermark portrait={portrait}/>
  <div style={{position:'relative',zIndex:5,maxWidth:portrait?930:1050}}><Eyebrow portrait={portrait}>Housing transmission</Eyebrow><Title size={portrait?64:53} style={{marginTop:14}}>{mechanism?'A benchmark, not a one-for-one pass-through.':'Mortgage rates kept climbing.'}</Title></div>
  {!mechanism?<div style={{position:'absolute',left:portrait?70:95,right:portrait?70:720,top:portrait?600:390,display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:14,zIndex:5}}>{mortgages.map((m,i)=><div key={m.date} style={{padding:portrait?'24px 12px':'22px 18px',background:'rgba(4,17,27,.94)',borderBottom:`${Math.max(4,chart*70+i*8)}px solid ${i===2?BRAND.copper:BRAND.teal}`,opacity:p(f,32+i*25,65+i*25)}}><div style={{fontSize:portrait?20:17,color:BRAND.muted,fontWeight:800}}>{m.date}</div><div style={{fontSize:portrait?44:38,fontWeight:950,marginTop:7}}>{m.value.toFixed(2)}%</div></div>)}</div>:<div style={{position:'absolute',left:portrait?70:98,right:portrait?70:650,top:portrait?650:430,zIndex:5}}>{[['10Y TREASURY','benchmark'],['MORTGAGE PRICING','lender + market inputs'],['MONTHLY PAYMENT','household cash flow']].map(([a,b],i)=><Enter key={a} delay={28+i*40}><div style={{display:'flex',alignItems:'center',gap:18,marginTop:14}}><div style={{width:44,height:44,borderRadius:99,background:i===2?BRAND.copper:BRAND.teal,color:BRAND.navy,display:'grid',placeItems:'center',fontWeight:950}}>{i+1}</div><div style={{padding:'16px 20px',background:'rgba(4,17,27,.94)',borderLeft:`4px solid ${i===2?BRAND.copper:BRAND.teal}`,flex:1}}><b style={{fontSize:portrait?26:22}}>{a}</b><span style={{fontSize:portrait?22:18,color:BRAND.muted}}> — {b}</span></div></div></Enter>)}</div>}
  <Source portrait={portrait}>Freddie Mac PMMS • 30-year fixed: 6.43% → 6.49% → 6.55%, July 2–16, 2026</Source>
</Canvas>};

const SupplyScene:React.FC<{portrait?:boolean;auction?:boolean}>=({portrait=false,auction=false})=>{const f=useCurrentFrame();const reveal=p(f,48,98),bars=p(f,120,190);return <Canvas portrait={portrait}><AbsoluteFill><EditorialPhoto src={auction?TREASURY_A:CAPITOL_DUSK} position="center 48%"/><Scrim opacity={.7}/></AbsoluteFill><Watermark portrait={portrait}/>
  <div style={{position:'relative',zIndex:4,maxWidth:portrait?900:1080,marginTop:portrait?180:90}}><Eyebrow portrait={portrait}>Duration supply</Eyebrow><Title size={portrait?64:53} style={{marginTop:14}}>{auction?'The long end also has to clear supply.':'Borrowing keeps duration in the room.'}</Title><div style={{marginTop:portrait?50:30,opacity:reveal,transform:`translateY(${(1-reveal)*25}px)`}}><BigNumber portrait={portrait}>$671B</BigNumber><div style={{fontSize:portrait?27:23,color:BRAND.muted,marginTop:12}}>Treasury’s May estimate of Q3 privately held net marketable borrowing.</div></div>
  <div style={{marginTop:portrait?50:28,width:portrait?'92%':'78%',display:'flex',gap:10,alignItems:'end',height:100}}>{[.42,.57,.78,1].map((h,i)=><div key={i} style={{height:`${h*100*bars}%`,background:i===3?BRAND.copper:BRAND.teal,flex:1,minHeight:4}}/>)}</div></div>
  <Source portrait={portrait}>U.S. Treasury • May 4, 2026 marketable borrowing estimate • not a yield-causality claim</Source>
</Canvas>};

const BalanceSheetScene:React.FC<{portrait?:boolean}>=({portrait=false})=>{const f=useCurrentFrame();const cards=[['HOUSEHOLDS',HOUSE,'mortgage + cash flow'],['COMPANIES',TREASURY_B,'refinancing + valuation'],['SOVEREIGN',CAPITOL_FRONT,'issuance + duration']];return <Canvas portrait={portrait}><Watermark portrait={portrait}/><Eyebrow portrait={portrait}>The same curve • three balance sheets</Eyebrow><Title size={portrait?62:51} style={{marginTop:14}}>Duration eventually becomes cash flow.</Title><div style={{marginTop:portrait?64:42,display:'grid',gridTemplateColumns:portrait?'1fr':'repeat(3,1fr)',gap:portrait?18:20}}>{cards.map(([label,src,sub],i)=><Enter key={String(label)} delay={20+i*38}><div style={{height:portrait?250:340,position:'relative',overflow:'hidden',borderBottom:`5px solid ${i===2?BRAND.copper:BRAND.teal}`}}><EditorialPhoto src={String(src)} position="center 48%"/><Scrim opacity={.55}/><div style={{position:'absolute',left:22,right:22,bottom:20}}><div style={{fontSize:portrait?28:25,fontWeight:950}}>{label}</div><div style={{fontSize:portrait?21:18,color:BRAND.muted,marginTop:5}}>{sub}</div></div></div></Enter>)}</div><Source portrait={portrait}>Capital Chronicle analysis • mechanism only; no unsupported pass-through estimate</Source></Canvas>};

const CausalChainScene:React.FC<{portrait?:boolean}>=({portrait=false})=>{const f=useCurrentFrame();const nodes=[['CURVE','market price'],['DECOMPOSE','path + premium'],['TRANSMIT','credit + housing'],['CONFIRM','data over time']];return <Canvas portrait={portrait}><Grid/><Watermark portrait={portrait}/><Eyebrow portrait={portrait}>How to read the move</Eyebrow><Title size={portrait?63:52} style={{marginTop:14}}>Price first. Explanation second.</Title><div style={{position:'absolute',left:portrait?74:110,right:portrait?74:110,top:portrait?610:390,display:'grid',gridTemplateColumns:portrait?'1fr':'repeat(4,1fr)',gap:portrait?16:20}}>{nodes.map(([a,b],i)=>{const q=spring({frame:f-i*34,fps:30,config:{damping:18,stiffness:120}});return <div key={a} style={{padding:portrait?'20px 24px':'25px 22px',background:'rgba(12,30,42,.96)',borderTop:`5px solid ${i===3?BRAND.copper:BRAND.teal}`,opacity:q,transform:`translateY(${(1-q)*32}px)`}}><div style={{fontSize:portrait?28:24,fontWeight:950}}>{a}</div><div style={{fontSize:portrait?20:18,color:BRAND.muted,marginTop:7}}>{b}</div></div>})}</div><Source portrait={portrait}>Capital Chronicle analytical framework • observation, model, transmission, test</Source></Canvas>};

const ConfirmScene:React.FC<{portrait?:boolean;expanded?:boolean}>=({portrait=false,expanded=false})=>{const rows=[['CURVE BREADTH','Do long tenors keep leading?'],['TERM PREMIUM','Does the estimated premium—not just the expected path—rise?'],['MORTGAGES','Do financing benchmarks keep following?'],['AUCTION DEMAND','Does duration clear cleanly?']];return <Canvas portrait={portrait}><Grid/><Watermark portrait={portrait}/><Eyebrow portrait={portrait}>Confirm or challenge</Eyebrow><Title size={portrait?63:52} style={{marginTop:14}}>One close is a checkpoint.</Title><div style={{marginTop:portrait?70:42,display:'grid',gridTemplateColumns:portrait?'1fr':'1fr 1fr',gap:portrait?16:18}}>{rows.slice(0,expanded?4:3).map(([a,b],i)=><Enter key={a} delay={18+i*30}><div style={{padding:portrait?'22px 24px':'22px 26px',background:'rgba(12,30,42,.95)',borderLeft:`5px solid ${i===rows.length-1?BRAND.copper:BRAND.teal}`}}><div style={{fontSize:portrait?26:22,fontWeight:950}}>{a}</div><div style={{fontSize:portrait?21:18,lineHeight:1.28,color:BRAND.muted,marginTop:7}}>{b}</div></div></Enter>)}</div><Enter delay={145}><div style={{marginTop:portrait?28:22,fontSize:portrait?27:23,color:BRAND.copper,fontWeight:900}}>Challenge: 30Y below 5% + a narrowing 2s10s over several closes.</div></Enter><Source portrait={portrait}>Capital Chronicle test framework • conditions, not a forecast</Source></Canvas>};

const SourceTimeline:React.FC<{portrait?:boolean}>=({portrait=false})=>{const items=[['JUL 13','Treasury curve','official close'],['JUL 16','Mortgage rate','6.55%'],['NEXT','Auctions + closes','confirmation']];return <Canvas portrait={portrait}><Watermark portrait={portrait}/><Eyebrow portrait={portrait}>Three evidence layers</Eyebrow><Title size={portrait?62:52} style={{marginTop:14}}>Observed. Estimated. Then tested.</Title><div style={{marginTop:portrait?100:65,display:'grid',gridTemplateColumns:portrait?'1fr':'repeat(3,1fr)',gap:22}}>{items.map(([date,title,sub],i)=><Enter key={date} delay={20+i*38}><div style={{padding:portrait?'28px':'30px',borderTop:`5px solid ${i===2?BRAND.copper:BRAND.teal}`,background:'rgba(12,30,42,.94)'}}><div style={{fontSize:portrait?20:17,color:BRAND.teal,fontWeight:950,letterSpacing:2}}>{date}</div><div style={{fontSize:portrait?34:30,fontWeight:950,marginTop:10}}>{title}</div><div style={{fontSize:portrait?23:20,color:BRAND.muted,marginTop:8}}>{sub}</div></div></Enter>)}</div><Source portrait={portrait}>Treasury • New York Fed ACM • Freddie Mac PMMS • Capital Chronicle synthesis</Source></Canvas>};

const shortCuts:[number,React.ReactNode][]=[
  [0,<PhotoHook portrait/>],[150,<CurveScene portrait/>],[390,<EvidenceScene portrait/>],[600,<DecompositionScene portrait/>],
  [840,<MortgageScene portrait/>],[1080,<SupplyScene portrait/>],[1320,<BalanceSheetScene portrait/>],[1530,<ConfirmScene portrait/>],[1770,<PhotoHook portrait closing/>]
];
export const AssetFirstTreasuryShort:React.FC<ProofProps>=()=> <AbsoluteFill>{shortCuts.map(([from,node],i)=><Sequence key={from} from={from} durationInFrames={(shortCuts[i+1]?.[0]??SHORT_FRAMES)-from} premountFor={30}>{node}</Sequence>)}</AbsoluteFill>;

const midCuts:[number,React.ReactNode][]=[
  [0,<PhotoHook/>],[180,<CurveScene/>],[510,<CurveScene delta/>],[810,<EvidenceScene/>],
  [1170,<DecompositionScene wide/>],[1500,<CausalChainScene/>],[1860,<MortgageScene/>],[2190,<MortgageScene mechanism/>],
  [2520,<SupplyScene/>],[2850,<BalanceSheetScene/>],[3180,<SupplyScene auction/>],[3510,<ConfirmScene expanded/>],
  [3900,<SourceTimeline/>],[4230,<PhotoHook closing/>]
];
export const AssetFirstTreasuryMidform:React.FC<ProofProps>=()=> <AbsoluteFill>{midCuts.map(([from,node],i)=><Sequence key={from} from={from} durationInFrames={(midCuts[i+1]?.[0]??MIDFORM_FRAMES)-from} premountFor={30}>{node}</Sequence>)}</AbsoluteFill>;
