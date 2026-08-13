import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, Easing, Sequence} from 'remotion';

export type AuthoredShotProps = {
  frame: number; fps: number; width: number; height: number; progress: number;
  assetPath?: string; assetClass?: string; narration: string; sourceLabel: string;
};

const Shot_s01: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => { const padX=width*0.08; const padY=height*0.1; const advance=interpolate(progress,[0,0.18,0.68,1],[0,0.08,1,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.out(Easing.cubic)}); const obstruction=interpolate(progress,[0.64,0.72],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}); const pulse=0.55+Math.sin(frame*0.22)*0.18; const endY=height*0.31+(height*0.46)*advance; const endWidth=5+advance*15; return <AbsoluteFill style={{background:'#050607',color:'#f4ead7',overflow:'hidden'}}><svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{position:'absolute',inset:0}}><defs><linearGradient id='s01-channel' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stopColor='#0b2030'/><stop offset='1' stopColor='#123b56'/></linearGradient><linearGradient id='s01-route' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stopColor='#ffcf73' stopOpacity='0.45'/><stop offset='1' stopColor='#f3a629'/></linearGradient></defs><path d={`M ${width*0.44} ${height*0.18} L ${width*0.27} ${height*0.84} L ${width*0.73} ${height*0.84} L ${width*0.56} ${height*0.18} Z`} fill='url(#s01-channel)' opacity='0.92'/><path d={`M ${width*0.5} ${height*0.22} L ${width*0.5} ${endY}`} stroke='url(#s01-route)' strokeWidth={endWidth} strokeLinecap='round' fill='none'/><ellipse cx={width*0.5} cy={endY} rx={8+advance*22} ry={3+advance*7} fill='#ffbd48' opacity={pulse}/><g opacity={obstruction} transform={`translate(${width*0.5} ${height*0.79})`}><circle r={36} fill='#19090a' stroke='#e34c3e' strokeWidth={5}/><path d='M -14 -14 L 14 14 M 14 -14 L -14 14' stroke='#ff6655' strokeWidth={7} strokeLinecap='round'/></g></svg><div style={{position:'absolute',left:padX,right:padX,bottom:padY,fontFamily:'monospace',fontSize:Math.max(17,width*0.019),letterSpacing:'0.15em',color:'#8e9aa0',textTransform:'uppercase'}}>{sourceLabel}</div></AbsoluteFill>; };

const Shot_s02: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => { const padX=width*0.08; const padY=height*0.1; const wipe=interpolate(progress,[0,0.22],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.out(Easing.cubic)}); const scan=interpolate(progress,[0.12,0.82],[0.12,0.72],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.cubic)}); const bracketW=width*0.22; const bracketH=height*0.34; const x=padX+(width-padX*2-bracketW)*scan; const y=height*0.31; return <AbsoluteFill style={{background:'#060809',color:'#f3ead9',overflow:'hidden'}}><div style={{position:'absolute',inset:0,clipPath:`inset(${(1-wipe)*100}% 0 0 0)`}}>{assetPath?<Img className={assetClass} src={staticFile(assetPath.replaceAll('\\','/'))} style={{width:'100%',height:'100%',objectFit:'cover',objectPosition:'76% center',filter:'saturate(0.72) contrast(1.12) brightness(0.72)',transform:'scale(1.32)'}}/>:null}<div style={{position:'absolute',inset:0,background:'linear-gradient(180deg,rgba(3,6,8,0.48),rgba(3,6,8,0.08) 45%,rgba(3,6,8,0.72))'}}/></div><div style={{position:'absolute',left:x,top:y,width:bracketW,height:bracketH,borderLeft:`${Math.max(4,width*0.005)}px solid #f2a72d`,borderRight:`${Math.max(4,width*0.005)}px solid #f2a72d`,boxShadow:'0 0 28px rgba(242,167,45,0.18)'}}><div style={{position:'absolute',left:0,right:0,top:0,height:4,background:'#f2a72d'}}/><div style={{position:'absolute',left:0,right:0,bottom:0,height:4,background:'#f2a72d'}}/></div><div style={{position:'absolute',left:padX,right:padX,bottom:padY,fontFamily:'monospace',fontSize:Math.max(17,width*0.019),letterSpacing:'0.15em',color:'#d4c4a5',textTransform:'uppercase'}}>{sourceLabel}</div></AbsoluteFill>; };

const Shot_s03: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => { const padX=width*0.08; const padY=height*0.1; const enter=interpolate(progress,[0,0.18],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.out(Easing.cubic)}); const channelLeft=width*0.34; const channelRight=width*0.66; const travelTop=height*0.19; const travelSpan=height*0.61; const dots=Array.from({length:6},(_,i)=>{ const direction=i%2===0?1:-1; const phase=((frame/fps*0.19+i/6)%1+1)%1; const t=direction===1?phase:1-phase; const y=travelTop+t*travelSpan; const x=width*0.5+Math.sin(t*Math.PI*1.6+i)*width*0.018; return {x,y,direction}; }); return <AbsoluteFill style={{background:'#071016',color:'#eee6d6',overflow:'hidden',clipPath:`inset(0 ${(1-enter)*100}% 0 0)`}}><svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{position:'absolute',inset:0}}><defs><linearGradient id='s03-water' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stopColor='#12384e'/><stop offset='0.5' stopColor='#0c2a3b'/><stop offset='1' stopColor='#16465e'/></linearGradient></defs><rect x={channelLeft} y={height*0.08} width={channelRight-channelLeft} height={height*0.82} rx={width*0.06} fill='url(#s03-water)'/><path d={`M 0 0 H ${width*0.43} C ${width*0.4} ${height*0.23},${width*0.31} ${height*0.36},${channelLeft} ${height*0.49} C ${width*0.37} ${height*0.65},${width*0.27} ${height*0.77},${width*0.3} ${height} H 0 Z`} fill='#12191b'/><path d={`M ${width} 0 H ${width*0.57} C ${width*0.6} ${height*0.23},${width*0.69} ${height*0.36},${channelRight} ${height*0.49} C ${width*0.63} ${height*0.65},${width*0.73} ${height*0.77},${width*0.7} ${height} H ${width} Z`} fill='#151c1d'/><path d={`M ${width*0.5} ${height*0.16} L ${width*0.5} ${height*0.84}`} stroke='#d99222' strokeWidth={3} strokeDasharray='10 18' opacity='0.4'/>{dots.map((dot,i)=><g key={i} transform={`translate(${dot.x} ${dot.y}) rotate(${dot.direction===1?0:180})`}><rect x={-14} y={-25} width={28} height={50} rx={13} fill='#f0a62d'/><path d='M -7 -9 H 7 M -7 1 H 7 M -5 11 H 5' stroke='#5d3b0c' strokeWidth={3}/><path d='M 0 -34 L -8 -23 H 8 Z' fill='#ffd37a'/></g>)}</svg><div style={{position:'absolute',left:padX,right:padX,bottom:padY,fontFamily:'monospace',fontSize:Math.max(17,width*0.019),letterSpacing:'0.15em',color:'#9eb2ba',textTransform:'uppercase'}}>{sourceLabel}</div></AbsoluteFill>; };

const Shot_s04: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => { const padX=width*0.08; const padY=height*0.1; const evidence=sourceLabel||'EIA PRESS RELEASE'; const parts=evidence.split('|'); const title=parts[0].trim(); const date=parts.slice(1).join(' | ').trim(); const typedCount=Math.floor(interpolate(progress,[0.08,0.55],[0,title.length],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})); const typed=title.slice(0,typedCount); const splitAt=Math.max(1,Math.ceil(title.length*0.52)); const lineOne=typed.slice(0,splitAt); const lineTwo=typed.slice(splitAt); const lock=interpolate(progress,[0.52,0.65],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.out(Easing.cubic)}); const routePulse=0.35+Math.sin(frame*0.12)*0.08; return <AbsoluteFill style={{background:'#071016',color:'#f5eddd',overflow:'hidden'}}><svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{position:'absolute',inset:0}}><rect x={width*0.34} y={height*0.06} width={width*0.32} height={height*0.84} rx={width*0.06} fill='#10364a'/><path d={`M 0 0 H ${width*0.43} C ${width*0.39} ${height*0.28},${width*0.32} ${height*0.39},${width*0.35} ${height} H 0 Z`} fill='#151b1c'/><path d={`M ${width} 0 H ${width*0.57} C ${width*0.61} ${height*0.28},${width*0.68} ${height*0.39},${width*0.65} ${height} H ${width} Z`} fill='#171d1e'/><path d={`M ${width*0.5} ${height*0.12} L ${width*0.5} ${height*0.78}`} stroke='#efaa35' strokeWidth={5} strokeDasharray='12 22' opacity={routePulse}/></svg><div style={{position:'absolute',left:padX,right:padX,bottom:padY,background:'rgba(5,8,9,0.94)',borderTop:'4px solid #e9a12d',padding:`${height*0.028}px ${width*0.045}px ${height*0.032}px`,boxShadow:'0 -24px 70px rgba(0,0,0,0.32)'}}><div style={{fontFamily:'Georgia,serif',fontSize:Math.max(34,width*0.047),lineHeight:1.08,letterSpacing:'-0.025em',minHeight:Math.max(92,height*0.085)}}><div>{lineOne}</div><div>{lineTwo}</div></div>{date?<div style={{marginTop:height*0.018,fontFamily:'monospace',fontSize:Math.max(18,width*0.022),letterSpacing:'0.14em',color:'#e8b75e',textTransform:'uppercase',opacity:lock,transform:`translateY(${(1-lock)*12}px)`}}>{date}</div>:null}</div></AbsoluteFill>; };

const Shot_s05: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => { const padX=width*0.08; const padY=height*0.1; const gap=(width-padX*2)/7; const valveY=height*0.49; const routeFill=interpolate(progress,[0.1,0.82],[0,0.88],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.cubic)}); const labelIn=interpolate(progress,[0.58,0.78],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}); return <AbsoluteFill style={{background:'radial-gradient(circle at 50% 48%,#132027 0%,#080b0d 58%,#050607 100%)',color:'#f3ebdb',overflow:'hidden'}}><svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{position:'absolute',inset:0}}><path d={`M ${padX} ${valveY} H ${width-padX}`} stroke='#273239' strokeWidth={18} strokeLinecap='round'/><path d={`M ${padX} ${valveY} H ${padX+(width-padX*2)*routeFill}`} stroke='#bd7617' strokeWidth={8} strokeLinecap='round'/>{Array.from({length:7},(_,i)=>{ const start=0.1+i*0.09; const lit=interpolate(progress,[start,start+0.09],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.out(Easing.cubic)}); const active=i===6?lit*0.2:lit; const x=padX+gap*(i+0.5); const glow=8+active*30; return <g key={i} transform={`translate(${x} ${valveY})`}><circle r={gap*0.31} fill='#0b0f11' stroke={active>0.55?'#f0a52a':'#374147'} strokeWidth={6}/><circle r={gap*0.19} fill='none' stroke={active>0.55?'#ffc75f':'#2c3438'} strokeWidth={8} style={{filter:`drop-shadow(0 0 ${glow}px rgba(240,165,42,${active*0.62}))`}}/><path d={`M ${-gap*0.14} 0 H ${gap*0.14} M 0 ${-gap*0.14} V ${gap*0.14}`} stroke={active>0.55?'#ffd585':'#465057'} strokeWidth={7} strokeLinecap='round'/><path d={`M 0 ${-gap*0.3} V ${-gap*0.48}`} stroke='#647078' strokeWidth={8}/></g>; })}</svg><div style={{position:'absolute',left:padX,right:padX,top:height*0.23,textAlign:'center',fontFamily:'Georgia,serif',fontSize:Math.max(34,width*0.05),lineHeight:1.05,opacity:labelIn,transform:`translateY(${(1-labelIn)*18}px)`}}>First quarter of 2027</div><div style={{position:'absolute',left:padX,right:padX,bottom:padY,fontFamily:'monospace',fontSize:Math.max(17,width*0.019),letterSpacing:'0.15em',color:'#9da6a9',textTransform:'uppercase'}}>{sourceLabel}</div></AbsoluteFill>; };

const Shot_s06: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const reveal = interpolate(progress,[0,0.14,0.86,1],[0,1,1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const ribbonY = interpolate(progress,[0,1],[18,-72]);
  const lineProgress = interpolate(progress,[0.18,0.82],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const lineLength = 760;
  return <AbsoluteFill style={{background:'#071014',color:'#f4efe4',overflow:'hidden',fontFamily:'Georgia, serif',opacity:reveal}}>
    <div style={{position:'absolute',inset:0,background:'radial-gradient(circle at 50% 42%, rgba(34,61,66,0.38), transparent 48%), linear-gradient(180deg,#081317 0%,#04090b 100%)'}} />
    <div style={{position:'absolute',left:width*0.29,top:height*0.1,width:width*0.42,height:height*0.8,overflow:'hidden',borderRadius:width*0.21,boxShadow:'0 0 0 1px rgba(244,239,228,0.16), 0 28px 90px rgba(0,0,0,0.5)',background:'#101b1e'}}>
      {assetPath ? <Img className={assetClass} src={staticFile(assetPath.replaceAll('\\','/'))} style={{position:'absolute',left:0,top:-height*0.06,width:'100%',height:'112%',objectFit:'cover',transform:`translateY(${ribbonY}px)`,filter:'saturate(0.78) contrast(1.08) brightness(0.82)'}} /> : null}
      <div style={{position:'absolute',inset:0,background:'linear-gradient(90deg,rgba(3,9,11,0.58),transparent 24%,transparent 76%,rgba(3,9,11,0.58)), linear-gradient(180deg,rgba(3,9,11,0.4),transparent 18%,transparent 82%,rgba(3,9,11,0.46))'}} />
    </div>
    <svg viewBox="0 0 1080 1920" style={{position:'absolute',inset:0,width:'100%',height:'100%'}}>
      <defs><filter id="s06glow"><feGaussianBlur stdDeviation="9" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
      <path d="M 90 1245 C 245 1228, 330 1165, 438 1085 S 690 900, 990 820" fill="none" stroke="rgba(239,164,55,0.16)" strokeWidth="20" strokeLinecap="round" />
      <path d="M 90 1245 C 245 1228, 330 1165, 438 1085 S 690 900, 990 820" fill="none" stroke="#efa437" strokeWidth="7" strokeLinecap="round" pathLength={lineLength} strokeDasharray={lineLength} strokeDashoffset={lineLength*(1-lineProgress)} filter="url(#s06glow)" />
      <circle cx={interpolate(lineProgress,[0,1],[90,990])} cy={interpolate(lineProgress,[0,1],[1245,820])} r="8" fill="#ffd17a" opacity={lineProgress>0&&lineProgress<1?1:0}/>
    </svg>
    {sourceLabel ? <div style={{position:'absolute',left:width*0.08,right:width*0.08,bottom:height*0.045,fontFamily:'Arial, sans-serif',fontSize:22,letterSpacing:1.8,textTransform:'uppercase',color:'rgba(244,239,228,0.52)',textAlign:'right'}}>{sourceLabel}</div> : null}
  </AbsoluteFill>;
};

const Shot_s07: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const split = interpolate(progress,[0,0.16],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const flow = interpolate(progress,[0.12,0.88],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const fill = interpolate(flow,[0,1],[0.04,0.62]);
  const activeDrops = Math.floor(interpolate(flow,[0,1],[2,9]));
  return <AbsoluteFill style={{background:'#061014',color:'#f3eee3',overflow:'hidden'}}>
    <div style={{position:'absolute',inset:0,background:'linear-gradient(90deg,#071116 0%,#071116 49.8%,#0d1718 50.2%,#0d1718 100%)'}} />
    <div style={{position:'absolute',left:'50%',top:height*0.1,bottom:height*0.1,width:2,background:'linear-gradient(180deg,transparent,rgba(239,164,55,0.58),transparent)',transform:`scaleY(${split})`}} />
    <svg viewBox="0 0 1080 1920" style={{position:'absolute',inset:0,width:'100%',height:'100%'}}>
      <defs>
        <linearGradient id="s07pipe" x1="0" y1="0" x2="1" y2="0"><stop stopColor="#26383b"/><stop offset="0.5" stopColor="#536366"/><stop offset="1" stopColor="#1d2d30"/></linearGradient>
        <linearGradient id="s07amber" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#ffd27c"/><stop offset="1" stopColor="#d57d18"/></linearGradient>
        <clipPath id="s07basin"><path d="M620 1210 L990 1210 L942 1590 Q805 1660 668 1590 Z"/></clipPath>
      </defs>
      <g opacity={split}>
        <path d="M95 790 H390 Q450 790 450 850 V1070" fill="none" stroke="url(#s07pipe)" strokeWidth="70" strokeLinecap="round" />
        <path d="M95 790 H390 Q450 790 450 850 V1070" fill="none" stroke="#061014" strokeWidth="38" strokeLinecap="round" />
        <ellipse cx="450" cy="1080" rx="48" ry="18" fill="#0c171a" stroke="#536366" strokeWidth="8" />
        <path d="M620 1210 L990 1210 L942 1590 Q805 1660 668 1590 Z" fill="#111e20" stroke="#68777a" strokeWidth="9" />
        <rect x="610" y={1598-(390*fill)} width="390" height={390*fill} fill="url(#s07amber)" opacity="0.88" clipPath="url(#s07basin)" />
        <path d={`M655 ${1598-(390*fill)} Q805 ${1577-(390*fill)} 955 ${1598-(390*fill)}`} fill="none" stroke="#ffd485" strokeWidth="7" clipPath="url(#s07basin)" />
        {Array.from({length:9}).map((_,i)=>{
          const visible=i<activeDrops;
          const spacing=flow<0.38?19:10;
          const cycle=((frame-i*spacing)%(spacing*activeDrops+1))/(spacing*activeDrops+1);
          const y=1040+cycle*215;
          const x=805+Math.sin(i*2.4)*7;
          return visible?<path key={i} d={`M${x} ${y-18} C${x-13} ${y+2},${x-11} ${y+19},${x} ${y+25} C${x+11} ${y+19},${x+13} ${y+2},${x} ${y-18}Z`} fill="#efa437" opacity={0.55+cycle*0.45}/>:null;
        })}
      </g>
    </svg>
    <div style={{position:'absolute',left:width*0.08,top:height*0.12,width:width*0.34,height:2,background:'rgba(244,239,228,0.2)',transform:`scaleX(${split})`,transformOrigin:'left'}} />
    <div style={{position:'absolute',right:width*0.08,top:height*0.12,width:width*0.34,height:2,background:'rgba(239,164,55,0.32)',transform:`scaleX(${split})`,transformOrigin:'right'}} />
    {sourceLabel ? <div style={{position:'absolute',left:width*0.08,right:width*0.08,bottom:height*0.045,fontFamily:'Arial, sans-serif',fontSize:22,letterSpacing:1.8,textTransform:'uppercase',color:'rgba(244,239,228,0.52)',textAlign:'right'}}>{sourceLabel}</div> : null}
  </AbsoluteFill>;
};

const Shot_s08: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const intro = spring({frame,fps,config:{damping:18,stiffness:95,mass:0.9}});
  const needlePhase = progress*Math.PI*3.2;
  const needleX = width*0.5+Math.sin(needlePhase)*width*0.324;
  const lineY = height*0.59;
  const rowHeight = height*0.068;
  const rowGap = height*0.018;
  const wordOpacity = (start:number)=>interpolate(progress,[start,start+0.1],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const supplyOpacity = wordOpacity(0.03);
  const inventoriesOpacity = wordOpacity(0.2);
  const demandOpacity = wordOpacity(0.37);
  const typeface = '"Franklin Gothic Medium", "Arial Narrow", sans-serif';
  const rowStyle: React.CSSProperties = {
    position:'absolute',
    left:0,
    right:0,
    height:rowHeight,
    display:'flex',
    alignItems:'center',
    overflow:'hidden',
    borderTop:'1px solid rgba(245,239,226,0.16)',
    borderBottom:'1px solid rgba(245,239,226,0.08)',
    background:'linear-gradient(90deg,rgba(255,255,255,0.025),rgba(255,255,255,0.065) 50%,rgba(255,255,255,0.025))'
  };
  return <AbsoluteFill style={{background:'#071114',color:'#f5efe2',overflow:'hidden'}}>
    <div style={{position:'absolute',inset:0,background:'radial-gradient(ellipse at 50% 50%,rgba(39,65,65,0.52),transparent 58%), repeating-linear-gradient(90deg,transparent 0,transparent 89px,rgba(255,255,255,0.018) 90px)'}} />
    <div style={{position:'absolute',left:width*0.08,right:width*0.08,top:height*0.215,height:rowHeight*3+rowGap*2,transform:`translateY(${(1-intro)*height*0.035}px)`,opacity:intro}}>
      <div style={{...rowStyle,top:0,justifyContent:'flex-start'}}>
        <div style={{width:10,height:10,borderRadius:'50%',background:'#9aa8a6',marginLeft:4,marginRight:30,flex:'0 0 auto'}} />
        <div style={{fontFamily:typeface,fontWeight:700,fontSize:width*0.057,lineHeight:1,letterSpacing:width*0.0048,color:'#dfe4df',whiteSpace:'nowrap',opacity:supplyOpacity,transform:`translateX(${(1-supplyOpacity)*-28}px)`}}>SUPPLY</div>
      </div>
      <div style={{...rowStyle,top:rowHeight+rowGap,justifyContent:'center',borderTop:'1px solid rgba(239,164,55,0.42)',borderBottom:'1px solid rgba(239,164,55,0.25)',background:'linear-gradient(90deg,rgba(239,164,55,0.015),rgba(239,164,55,0.13) 50%,rgba(239,164,55,0.015))'}}>
        <div style={{fontFamily:typeface,fontWeight:700,fontSize:width*0.063,lineHeight:1,letterSpacing:width*0.0038,color:'#ffd17a',whiteSpace:'nowrap',opacity:inventoriesOpacity}}>INVENTORIES</div>
      </div>
      <div style={{...rowStyle,top:(rowHeight+rowGap)*2,justifyContent:'flex-end'}}>
        <div style={{fontFamily:typeface,fontWeight:700,fontSize:width*0.057,lineHeight:1,letterSpacing:width*0.0048,color:'#dfe4df',whiteSpace:'nowrap',opacity:demandOpacity,transform:`translateX(${(1-demandOpacity)*28}px)`}}>DEMAND</div>
        <div style={{width:10,height:10,borderRadius:'50%',background:'#9aa8a6',marginLeft:30,marginRight:4,flex:'0 0 auto'}} />
      </div>
    </div>
    <div style={{position:'absolute',left:width*0.08,right:width*0.08,top:lineY,height:8,borderRadius:8,background:'linear-gradient(90deg,#405054,#efa437 50%,#405054)',boxShadow:'0 0 28px rgba(239,164,55,0.16)',opacity:intro}} />
    {[0,0.5,1].map((x,i)=><div key={i} style={{position:'absolute',left:width*0.08+(width*0.84)*x-2,top:lineY-height*0.012,width:4,height:height*0.024,background:i===1?'#efa437':'#647276',opacity:intro}} />)}
    <svg viewBox={`0 0 ${width} ${height}`} style={{position:'absolute',inset:0,width:'100%',height:'100%',opacity:intro}}>
      <defs><filter id="s08glow"><feGaussianBlur stdDeviation="8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
      <path d={`M ${needleX} ${lineY-height*0.085} L ${needleX-width*0.028} ${lineY-2} L ${needleX+width*0.028} ${lineY-2} Z`} fill="#efa437" filter="url(#s08glow)" />
      <circle cx={needleX} cy={lineY} r={width*0.016} fill="#ffd17a" />
    </svg>
  </AbsoluteFill>;
};

const Shot_s09: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const wipe = interpolate(progress,[0,0.24],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const contour = interpolate(progress,[0.12,0.9],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const pathLength = 1040;
  const diagonal = 18+wipe*118;
  return <AbsoluteFill style={{background:'#050b0e',overflow:'hidden'}}>
    <div style={{position:'absolute',inset:0,background:'radial-gradient(circle at 60% 43%,rgba(41,61,61,0.42),transparent 55%)'}} />
    <div style={{position:'absolute',left:width*0.08,right:width*0.08,top:height*0.1,bottom:height*0.1,overflow:'hidden',border:'1px solid rgba(244,239,228,0.14)',boxShadow:'0 35px 100px rgba(0,0,0,0.48)',clipPath:`polygon(0 0, ${diagonal}% 0, ${Math.max(0,diagonal-36)}% 100%, 0 100%)`}}>
      {assetPath ? <Img className={assetClass} src={staticFile(assetPath.replaceAll('\\','/'))} style={{width:'100%',height:'100%',objectFit:'contain',objectPosition:'center center',background:'#f4f1e9',filter:'saturate(0.78) contrast(1.12) brightness(0.88)'}} /> : null}
      <div style={{position:'absolute',inset:0,background:'linear-gradient(180deg,rgba(4,10,12,0.16),rgba(4,10,12,0.38)), linear-gradient(90deg,rgba(4,10,12,0.38),transparent 18%,transparent 82%,rgba(4,10,12,0.38))'}} />
    </div>
    <svg viewBox="0 0 1080 1920" style={{position:'absolute',inset:0,width:'100%',height:'100%'}}>
      <defs><filter id="s09glow"><feGaussianBlur stdDeviation="8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
      <path d="M110 1370 C190 1280 242 1325 310 1190 C382 1048 445 1132 515 980 C586 826 660 920 728 760 C794 607 872 700 970 510" fill="none" stroke="rgba(239,164,55,0.18)" strokeWidth="22" strokeLinecap="round" />
      <path d="M110 1370 C190 1280 242 1325 310 1190 C382 1048 445 1132 515 980 C586 826 660 920 728 760 C794 607 872 700 970 510" fill="none" stroke="#efa437" strokeWidth="7" strokeLinecap="round" pathLength={pathLength} strokeDasharray={pathLength} strokeDashoffset={pathLength*(1-contour)} filter="url(#s09glow)" />
      <circle cx="970" cy="510" r={10*contour} fill="#ffd17a" opacity={contour}/>
    </svg>
    {sourceLabel ? <div style={{position:'absolute',left:width*0.08,right:width*0.08,bottom:height*0.045,fontFamily:'Arial, sans-serif',fontSize:22,letterSpacing:1.8,textTransform:'uppercase',color:'rgba(244,239,228,0.52)',textAlign:'right'}}>{sourceLabel}</div> : null}
  </AbsoluteFill>;
};

const Shot_s10: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const enter = spring({frame,fps,config:{damping:20,stiffness:110,mass:0.85}});
  const stages=[{label:'JUNE',x:190,y:590,start:0.04},{label:'Q3 2026',x:470,y:930,start:0.27},{label:'2027',x:750,y:1270,start:0.5}];
  return <AbsoluteFill style={{background:'#061014',color:'#f5efe2',overflow:'hidden'}}>
    <div style={{position:'absolute',inset:0,background:'linear-gradient(145deg,rgba(28,52,54,0.42),transparent 46%), radial-gradient(circle at 72% 68%,rgba(239,164,55,0.09),transparent 35%)'}} />
    <svg viewBox="0 0 1080 1920" style={{position:'absolute',inset:0,width:'100%',height:'100%',opacity:enter}}>
      <defs>
        <filter id="s10glow"><feGaussianBlur stdDeviation="8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
        <linearGradient id="s10path" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#ffd17a"/><stop offset="1" stopColor="#d67d1b"/></linearGradient>
      </defs>
      <path d="M95 390 C270 510 320 690 430 820 S650 1090 985 1470" fill="none" stroke="rgba(239,164,55,0.15)" strokeWidth="24" strokeLinecap="round" />
      <path d="M95 390 C270 510 320 690 430 820 S650 1090 985 1470" fill="none" stroke="url(#s10path)" strokeWidth="8" strokeLinecap="round" filter="url(#s10glow)" />
      {stages.map((stage,i)=>{
        const local=interpolate(progress,[stage.start,stage.start+0.2],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
        const shift=(1-local)*110;
        return <g key={stage.label} transform={`translate(${shift} 0)`} opacity={local}>
          <rect x={stage.x-82} y={stage.y-105} width="260" height="170" rx="8" fill="rgba(7,17,20,0.86)" stroke={i===1?'#efa437':'rgba(244,239,228,0.45)'} strokeWidth="3" />
          <path d={`M${stage.x-82} ${stage.y+65} H${stage.x+178}`} stroke="#efa437" strokeWidth="8" />
          <circle cx={stage.x} cy={stage.y} r="14" fill="#ffd17a" />
          <text x={stage.x+48} y={stage.y+12} fill="#f5efe2" fontFamily="Arial, sans-serif" fontWeight="700" fontSize="42" letterSpacing="2">{stage.label}</text>
        </g>;
      })}
    </svg>
    <div style={{position:'absolute',left:width*0.08,top:height*0.1,width:width*0.84,height:2,background:'linear-gradient(90deg,rgba(239,164,55,0.55),transparent)',transform:`scaleX(${enter})`,transformOrigin:'left'}} />
    {sourceLabel ? <div style={{position:'absolute',left:width*0.08,right:width*0.08,bottom:height*0.045,fontFamily:'Arial, sans-serif',fontSize:22,letterSpacing:1.8,textTransform:'uppercase',color:'rgba(244,239,228,0.52)',textAlign:'right'}}>{sourceLabel}</div> : null}
  </AbsoluteFill>;
};

const Shot_s11: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const unit = Math.min(width / 1080, height / 1920);
  const intro = interpolate(progress, [0, 0.14], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const outro = interpolate(progress, [0.9, 1], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const highFill = interpolate(frame, [fps * 0.35, fps * 1.45], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const lowFill = interpolate(frame, [fps * 1.35, fps * 2.65], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const liquidBand = interpolate(progress, [0, 0.18], [100, -22], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
  const amber = '#F2A51A';
  const ink = '#132938';
  const cream = '#F3E9D5';
  return <AbsoluteFill style={{backgroundColor: ink, overflow: 'hidden', color: cream, fontFamily: 'Georgia, Times New Roman, serif', opacity: outro}}>
    <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(circle at 50% 76%, rgba(242,165,26,0.16), transparent 43%), linear-gradient(150deg, #17394A 0%, #102531 68%, #0B1A22 100%)'}} />
    <div style={{position: 'absolute', left: 0, right: 0, top: `${liquidBand}%`, height: 130 * unit, background: 'linear-gradient(180deg, rgba(242,165,26,0), rgba(242,165,26,0.34), rgba(242,165,26,0))', transform: 'skewY(-5deg)', pointerEvents: 'none'}} />
    <div style={{position: 'absolute', left: width * 0.08, right: width * 0.08, top: height * 0.105, opacity: intro}}>
      <div style={{fontFamily: 'Arial Narrow, sans-serif', fontSize: 24 * unit, fontWeight: 700, letterSpacing: 5 * unit, color: amber}}>GASOLINE FORECAST</div>
      <div style={{marginTop: 18 * unit, width: 90 * unit, height: 5 * unit, backgroundColor: amber}} />
    </div>
    <svg viewBox='0 0 1080 1260' style={{position: 'absolute', left: width * 0.08, top: height * 0.19, width: width * 0.84, height: height * 0.66, overflow: 'visible', opacity: intro}}>
      <defs>
        <clipPath id='s11-pump-a'><path d='M95 170 Q95 105 160 105 H365 Q430 105 430 170 V780 H95 Z' /></clipPath>
        <clipPath id='s11-pump-b'><path d='M650 170 Q650 105 715 105 H920 Q985 105 985 170 V780 H650 Z' /></clipPath>
      </defs>
      <path d='M95 780 V170 Q95 105 160 105 H365 Q430 105 430 170 V780 M95 780 H430 M150 170 H375 V360 H150 Z M430 245 C535 245 505 500 565 500 V640' fill='none' stroke={amber} strokeWidth='25' strokeLinejoin='round' strokeLinecap='round' />
      <path d='M650 780 V170 Q650 105 715 105 H920 Q985 105 985 170 V780 M650 780 H985 M705 170 H930 V360 H705 Z M985 245 C1060 245 1035 500 1055 500 V640' fill='none' stroke={amber} strokeWidth='25' strokeLinejoin='round' strokeLinecap='round' />
      <rect x='105' y={770 - highFill * 555} width='315' height={highFill * 555} fill={amber} opacity='0.88' clipPath='url(#s11-pump-a)' />
      <rect x='660' y={770 - lowFill * 425} width='315' height={lowFill * 425} fill={amber} opacity='0.88' clipPath='url(#s11-pump-b)' />
      <line x1='125' y1='215' x2='400' y2='215' stroke={cream} strokeWidth='7' opacity='0.72' />
      <line x1='680' y1='345' x2='955' y2='345' stroke={cream} strokeWidth='7' opacity='0.72' />
      <text x='262' y='930' textAnchor='middle' fill={cream} fontFamily='Arial Narrow, sans-serif' fontSize='38' fontWeight='700' letterSpacing='7'>Q3</text>
      <text x='817' y='930' textAnchor='middle' fill={cream} fontFamily='Arial Narrow, sans-serif' fontSize='38' fontWeight='700' letterSpacing='7'>Q4</text>
      <text x='262' y='1045' textAnchor='middle' fill={cream} fontFamily='Georgia, serif' fontSize='100' fontWeight='700'>$3.80</text>
      <text x='817' y='1045' textAnchor='middle' fill={cream} fontFamily='Georgia, serif' fontSize='100' fontWeight='700'>$3.40</text>
      <text x='540' y='1135' textAnchor='middle' fill={amber} fontFamily='Arial Narrow, sans-serif' fontSize='29' fontWeight='700' letterSpacing='6'>PER GALLON</text>
    </svg>
    {sourceLabel ? <div style={{position: 'absolute', left: width * 0.08, bottom: height * 0.045, fontFamily: 'Arial Narrow, sans-serif', fontSize: 18 * unit, fontWeight: 700, letterSpacing: 2.4 * unit, color: 'rgba(243,233,213,0.58)'}}>SOURCE · {sourceLabel}</div> : null}
  </AbsoluteFill>;
};

const Shot_s12: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const unit = Math.min(width / 1080, height / 1920);
  const fadeIn = interpolate(progress, [0, 0.16], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const inflationAngle = interpolate(frame, [fps * 0.35, fps * 2.25], [-52, 37], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
  const policyPhase = interpolate(frame, [fps * 1.0, fps * 2.8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const policyAngle = -2 + Math.sin(policyPhase * Math.PI * 2) * 18 * (1 - policyPhase * 0.55);
  const suspended = interpolate(frame, [fps * 2.4, fps * 3.35], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const amber = '#E8A11D';
  const ink = '#162B35';
  const paper = '#F0E8D8';
  return <AbsoluteFill style={{backgroundColor: paper, overflow: 'hidden', color: ink, fontFamily: 'Georgia, Times New Roman, serif'}}>
    <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(circle at 18% 18%, rgba(232,161,29,0.18), transparent 34%), linear-gradient(180deg, #F4EDDF 0%, #E9DFCD 100%)', opacity: fadeIn}} />
    <div style={{position: 'absolute', left: width * 0.08, right: width * 0.08, top: height * 0.105, opacity: fadeIn}}>
      <div style={{fontFamily: 'Arial Narrow, sans-serif', fontSize: 24 * unit, fontWeight: 700, letterSpacing: 5 * unit, color: '#A56A0A'}}>LOWER GASOLINE PRICES</div>
      <div style={{marginTop: 26 * unit, fontSize: 66 * unit, lineHeight: 0.98, fontWeight: 700, maxWidth: width * 0.75}}>Relief is not<br/>resolution.</div>
    </div>
    <svg viewBox='0 0 1080 1120' style={{position: 'absolute', left: width * 0.08, top: height * 0.31, width: width * 0.84, height: height * 0.56, opacity: fadeIn, overflow: 'visible'}}>
      <path d='M90 485 A360 360 0 0 1 810 485' fill='none' stroke='#D3C8B5' strokeWidth='62' strokeLinecap='round' />
      <path d='M90 485 A360 360 0 0 1 810 485' fill='none' stroke={amber} strokeWidth='18' strokeLinecap='round' strokeDasharray='18 22' opacity='0.72' />
      <g transform={`translate(450 485) rotate(${inflationAngle})`}>
        <line x1='-15' y1='0' x2='0' y2='-292' stroke={amber} strokeWidth='22' strokeLinecap='round' />
      </g>
      <circle cx='450' cy='485' r='36' fill={amber} />
      <circle cx='450' cy='485' r='14' fill={paper} />
      <text x='450' y='610' textAnchor='middle' fill={ink} fontFamily='Arial Narrow, sans-serif' fontSize='38' fontWeight='700' letterSpacing='6'>HEADLINE INFLATION</text>
      <line x1='135' y1='690' x2='765' y2='690' stroke='#C9BDAA' strokeWidth='3' />
      <circle cx='450' cy='890' r='158' fill={ink} />
      <path d='M335 912 A120 120 0 0 1 565 912' fill='none' stroke={paper} strokeWidth='10' opacity='0.48' strokeLinecap='round' />
      <g transform={`translate(450 912) rotate(${policyAngle})`}>
        <line x1='0' y1='14' x2='0' y2='-112' stroke={paper} strokeWidth='18' strokeLinecap='round' />
      </g>
      <circle cx='450' cy='912' r='23' fill={paper} />
      <text x='450' y='1085' textAnchor='middle' fill={ink} fontFamily='Arial Narrow, sans-serif' fontSize='35' fontWeight='700' letterSpacing='5'>BROADER POLICY</text>
      <text x='920' y='890' textAnchor='end' fill={ink} fontFamily='Georgia, serif' fontSize='44' fontStyle='italic' opacity={0.38 + suspended * 0.62}>unresolved</text>
      <line x1='770' y1='915' x2='920' y2='915' stroke={amber} strokeWidth='7' strokeDasharray='18 13' opacity={0.3 + suspended * 0.7} />
    </svg>
    {sourceLabel ? <div style={{position: 'absolute', left: width * 0.08, bottom: height * 0.045, fontFamily: 'Arial Narrow, sans-serif', fontSize: 18 * unit, fontWeight: 700, letterSpacing: 2.4 * unit, color: 'rgba(22,43,53,0.55)'}}>SOURCE · {sourceLabel}</div> : null}
  </AbsoluteFill>;
};

const Shot_s13: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const unit = Math.min(width / 1080, height / 1920);
  const stripDrop = interpolate(progress, [0, 0.16], [-180, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.back(1.2))});
  const firstPin = spring({frame: frame - fps * 0.55, fps, config: {damping: 13, stiffness: 165, mass: 0.7}});
  const secondPin = spring({frame: frame - fps * 1.45, fps, config: {damping: 13, stiffness: 165, mass: 0.7}});
  const route = interpolate(frame, [fps * 1.7, fps * 2.75], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
  const tear = interpolate(progress, [0.9, 1], [0, 90], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.cubic)});
  const amber = '#F0A51C';
  const blue = '#143A4A';
  const paper = '#F3E9D5';
  return <AbsoluteFill style={{backgroundColor: blue, overflow: 'hidden', color: blue, fontFamily: 'Georgia, Times New Roman, serif'}}>
    <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(145deg, #102D3A 0%, #1B4D5F 58%, #0F2935 100%)'}} />
    <div style={{position: 'absolute', left: width * 0.08, top: height * 0.105, color: paper, fontFamily: 'Arial Narrow, sans-serif', fontSize: 24 * unit, fontWeight: 700, letterSpacing: 5 * unit}}>NEXT CHECKPOINTS</div>
    <div style={{position: 'absolute', left: width * 0.08, right: width * 0.08, top: height * 0.19, bottom: height * 0.12, transform: `translateY(${stripDrop + tear}px)`, clipPath: 'polygon(0 2%, 4% 0, 8% 2%, 12% 0, 16% 2%, 20% 0, 24% 2%, 28% 0, 32% 2%, 36% 0, 40% 2%, 44% 0, 48% 2%, 52% 0, 56% 2%, 60% 0, 64% 2%, 68% 0, 72% 2%, 76% 0, 80% 2%, 84% 0, 88% 2%, 92% 0, 96% 2%, 100% 0, 100% 98%, 96% 100%, 92% 98%, 88% 100%, 84% 98%, 80% 100%, 76% 98%, 72% 100%, 68% 98%, 64% 100%, 60% 98%, 56% 100%, 52% 98%, 48% 100%, 44% 98%, 40% 100%, 36% 98%, 32% 100%, 28% 98%, 24% 100%, 20% 98%, 16% 100%, 12% 98%, 8% 100%, 4% 98%, 0 100%)', background: 'linear-gradient(180deg, #F6EDDC 0%, #E9DDC7 100%)', boxShadow: '0 35px 80px rgba(0,0,0,0.3)'}}>
      <div style={{position: 'absolute', left: '8%', right: '8%', top: '9%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontFamily: 'Arial Narrow, sans-serif', fontSize: 22 * unit, fontWeight: 700, letterSpacing: 4 * unit, color: 'rgba(20,58,74,0.55)'}}>
        <span>JULY</span><span>2026 RELEASE CALENDAR</span><span>AUGUST</span>
      </div>
      <svg viewBox='0 0 900 1120' style={{position: 'absolute', left: '5%', top: '15%', width: '90%', height: '78%', overflow: 'visible'}}>
        <line x1='170' y1='525' x2='730' y2='525' stroke='#B7AB97' strokeWidth='8' strokeLinecap='round' />
        <line x1='170' y1='525' x2={170 + route * 560} y2='525' stroke={amber} strokeWidth='12' strokeLinecap='round' />
        <circle cx='170' cy='525' r='24' fill={amber} />
        <circle cx='730' cy='525' r={14 + route * 10} fill={amber} opacity={0.25 + route * 0.75} />
        <g transform={`translate(170 ${-210 + firstPin * 210})`}>
          <path d='M0 0 C-70 0 -108 55 -108 112 C-108 198 0 292 0 292 C0 292 108 198 108 112 C108 55 70 0 0 0 Z' fill={amber} />
          <circle cx='0' cy='108' r='38' fill={paper} />
        </g>
        <g transform={`translate(730 ${-210 + secondPin * 210})`}>
          <path d='M0 0 C-70 0 -108 55 -108 112 C-108 198 0 292 0 292 C0 292 108 198 108 112 C108 55 70 0 0 0 Z' fill={amber} />
          <circle cx='0' cy='108' r='38' fill={paper} />
        </g>
        <text x='170' y='695' textAnchor='middle' fill={blue} fontFamily='Arial Narrow, sans-serif' fontSize='38' fontWeight='700' letterSpacing='6'>JUL</text>
        <text x='170' y='810' textAnchor='middle' fill={blue} fontFamily='Georgia, serif' fontSize='126' fontWeight='700'>15</text>
        <text x='170' y='875' textAnchor='middle' fill='#8D6012' fontFamily='Arial Narrow, sans-serif' fontSize='26' fontWeight='700' letterSpacing='3'>WEEKLY PETROLEUM</text>
        <text x='170' y='914' textAnchor='middle' fill='#8D6012' fontFamily='Arial Narrow, sans-serif' fontSize='26' fontWeight='700' letterSpacing='3'>STATUS REPORT</text>
        <text x='730' y='695' textAnchor='middle' fill={blue} fontFamily='Arial Narrow, sans-serif' fontSize='38' fontWeight='700' letterSpacing='6'>AUG</text>
        <text x='730' y='810' textAnchor='middle' fill={blue} fontFamily='Georgia, serif' fontSize='126' fontWeight='700'>11</text>
        <text x='730' y='875' textAnchor='middle' fill='#8D6012' fontFamily='Arial Narrow, sans-serif' fontSize='26' fontWeight='700' letterSpacing='3'>SHORT-TERM</text>
        <text x='730' y='914' textAnchor='middle' fill='#8D6012' fontFamily='Arial Narrow, sans-serif' fontSize='26' fontWeight='700' letterSpacing='3'>ENERGY OUTLOOK</text>
      </svg>
    </div>
    {sourceLabel ? <div style={{position: 'absolute', left: width * 0.08, bottom: height * 0.045, fontFamily: 'Arial Narrow, sans-serif', fontSize: 18 * unit, fontWeight: 700, letterSpacing: 2.4 * unit, color: 'rgba(243,233,213,0.58)'}}>SOURCE · {sourceLabel}</div> : null}
  </AbsoluteFill>;
};

const Shot_s14: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const unit = Math.min(width / 1080, height / 1920);
  const settle = interpolate(progress, [0, 0.2], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const tanker = interpolate(frame, [fps * 0.25, fps * 1.55], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
  const ripple = interpolate(frame, [fps * 1.35, fps * 2.35], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const statement = interpolate(frame, [fps * 1.7, fps * 2.55], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const black = interpolate(progress, [0.82, 1], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
  const amber = '#ECA31E';
  const blue = '#1B6077';
  const deep = '#0C2631';
  const paper = '#F1E8D8';
  return <AbsoluteFill style={{backgroundColor: deep, overflow: 'hidden', color: paper, fontFamily: 'Georgia, Times New Roman, serif'}}>
    <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 77%, rgba(236,163,30,0.2), transparent 48%), linear-gradient(180deg, #123B4B 0%, #0C2B37 54%, #081D26 100%)'}} />
    <div style={{position: 'absolute', left: width * 0.08, right: width * 0.08, top: height * 0.105, textAlign: 'center', opacity: statement, transform: `translateY(${(1 - statement) * 32 * unit}px)`}}>
      <div style={{fontFamily: 'Arial Narrow, sans-serif', fontSize: 24 * unit, fontWeight: 700, letterSpacing: 6 * unit, color: amber}}>THE TEST AHEAD</div>
      <div style={{marginTop: 24 * unit, fontSize: 76 * unit, lineHeight: 0.95, fontWeight: 700, letterSpacing: -2 * unit}}>RECOVERY<br/><span style={{color: amber}}>NEEDS PROOF.</span></div>
    </div>
    <svg viewBox='0 0 1080 1300' style={{position: 'absolute', left: width * 0.08, top: height * 0.31, width: width * 0.84, height: height * 0.62, opacity: settle, overflow: 'visible'}}>
      <path d='M470 -40 C475 160 420 300 350 430 C280 565 160 650 75 720 L75 820 C220 760 360 695 455 600 C520 535 545 470 540 390 C535 470 560 535 625 600 C720 695 860 760 1005 820 L1005 720 C920 650 800 565 730 430 C660 300 605 160 610 -40 Z' fill={blue} opacity='0.82' />
      <path d='M540 -40 C540 155 540 300 540 625' fill='none' stroke='#66AFC0' strokeWidth='18' strokeLinecap='round' opacity='0.75' />
      <ellipse cx='540' cy='855' rx='475' ry='250' fill={amber} opacity='0.88' />
      <ellipse cx='540' cy='810' rx='475' ry='220' fill='#F5B942' />
      <ellipse cx='540' cy='792' rx='420' ry='170' fill={amber} opacity='0.56' />
      <ellipse cx='540' cy='800' rx={90 + ripple * 285} ry={32 + ripple * 105} fill='none' stroke={paper} strokeWidth='8' opacity={0.72 * (1 - ripple)} />
      <ellipse cx='540' cy='800' rx={42 + ripple * 175} ry={15 + ripple * 66} fill='none' stroke='#FFF5DE' strokeWidth='5' opacity={0.52 * (1 - ripple)} />
      <circle cx='540' cy={-25 + tanker * 720} r='24' fill={paper} />
      <circle cx='540' cy={-25 + tanker * 720} r='40' fill='none' stroke={amber} strokeWidth='7' opacity='0.75' />
      <g opacity={statement}>
        <line x1='128' y1='1140' x2='952' y2='1140' stroke='rgba(241,232,216,0.28)' strokeWidth='3' />
        <text x='128' y='1225' fill={paper} fontFamily='Arial Narrow, sans-serif' fontSize='31' fontWeight='700' letterSpacing='5'>BARRELS</text>
        <text x='540' y='1225' textAnchor='middle' fill={paper} fontFamily='Arial Narrow, sans-serif' fontSize='31' fontWeight='700' letterSpacing='5'>INVENTORIES</text>
        <text x='952' y='1225' textAnchor='end' fill={paper} fontFamily='Arial Narrow, sans-serif' fontSize='31' fontWeight='700' letterSpacing='5'>DEMAND</text>
      </g>
    </svg>
    {sourceLabel ? <div style={{position: 'absolute', left: width * 0.08, bottom: height * 0.045, fontFamily: 'Arial Narrow, sans-serif', fontSize: 18 * unit, fontWeight: 700, letterSpacing: 2.4 * unit, color: 'rgba(241,232,216,0.55)'}}>SOURCE · {sourceLabel}</div> : null}
    <AbsoluteFill style={{backgroundColor: '#000000', opacity: black}} />
  </AbsoluteFill>;
};

const Shot_m01: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.min(1, Math.max(0, progress));
  const dustClear = interpolate(p, [0, 0.72, 1], [0, 1, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const push = interpolate(p, [0, 1], [-width * 0.08, width * 0.07], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const pulse = 0.5 + 0.5 * Math.sin(frame / Math.max(1, fps) * Math.PI * 1.4);
  const dust = [
    [0.17, 0.25, 18], [0.25, 0.67, 11], [0.39, 0.31, 13], [0.52, 0.74, 20],
    [0.68, 0.24, 12], [0.79, 0.65, 17], [0.88, 0.36, 9], [0.12, 0.78, 10]
  ];
  return <AbsoluteFill style={{backgroundColor: '#17191b', overflow: 'hidden', fontFamily: 'Georgia, serif', color: '#f2e7d2'}}>
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{position: 'absolute', inset: 0}}>
      <defs>
        <linearGradient id="m01Dust" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#c98535" stopOpacity="0.42" />
          <stop offset="1" stopColor="#6a3d20" stopOpacity="0.08" />
        </linearGradient>
        <filter id="m01Blur"><feGaussianBlur stdDeviation="18" /></filter>
      </defs>
      <path d={`M ${-width * 0.16 + push} ${height * 0.92} L ${width * 0.9 + push} ${height * 0.08}`} stroke="#39a9d6" strokeWidth={height * 0.105} opacity="0.16" filter="url(#m01Blur)" />
      <path d={`M ${-width * 0.16 + push} ${height * 0.92} L ${width * 0.9 + push} ${height * 0.08}`} stroke="#43b6df" strokeWidth={height * 0.035} opacity="0.9" />
      <path d={`M ${-width * 0.16 + push} ${height * 0.92} L ${width * 0.9 + push} ${height * 0.08}`} stroke="#d9f3fb" strokeWidth={height * 0.004} opacity={0.35 + pulse * 0.2} />
      <g opacity={1 - dustClear * 0.72}>
        {dust.map(([x, y, r], i) => <circle key={i} cx={width * x} cy={height * y} r={r} fill="url(#m01Dust)" />)}
      </g>
      <path d={`M ${width * 0.08 + push} ${height * 0.84} C ${width * 0.3 + push} ${height * 0.7}, ${width * 0.53 + push} ${height * 0.4}, ${width * 0.84 + push} ${height * 0.13}`} stroke="#d08a3e" strokeWidth={height * 0.16} opacity={0.1 + (1 - dustClear) * 0.18} filter="url(#m01Blur)" />
    </svg>
    <div style={{position: 'absolute', left: '8%', top: '10%', fontSize: 22, letterSpacing: 4, color: '#8c979b'}}>THE NEXT TEST</div>
    <div style={{position: 'absolute', left: '8%', bottom: '10%', width: '54%', fontSize: 40, lineHeight: 1.08, letterSpacing: 0.5}}>Can the route hold after the shock?</div>
    <div style={{position: 'absolute', right: '8%', bottom: '10%', fontFamily: 'Arial, sans-serif', fontSize: 18, letterSpacing: 2, color: '#8c979b'}}>{sourceLabel}</div>
  </AbsoluteFill>;
};

const Shot_m02: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.min(1, Math.max(0, progress));
  const flicker = 0.72 + 0.28 * Math.sin(frame / Math.max(1, fps) * Math.PI * 9);
  const lineEnd = interpolate(p, [0, 0.45, 1], [0.78, 0.6, 0.53], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const scrape = interpolate(p, [0, 1], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{backgroundColor: '#1b1c1e', overflow: 'hidden', fontFamily: 'Georgia, serif', color: '#f2e7d2'}}>
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{position: 'absolute', inset: 0}}>
      <defs>
        <linearGradient id="m02Channel" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stopColor="#287eaa" /><stop offset="1" stopColor="#3db5dc" /></linearGradient>
        <filter id="m02Soft"><feGaussianBlur stdDeviation="10" /></filter>
      </defs>
      <path d={`M 0 ${height * 0.82} L ${width * lineEnd} ${height * 0.34}`} stroke="#4ab9df" strokeWidth={height * 0.11} opacity="0.18" filter="url(#m02Soft)" />
      <path d={`M 0 ${height * 0.82} L ${width * lineEnd} ${height * 0.34}`} stroke="url(#m02Channel)" strokeWidth={height * 0.035} opacity="0.94" />
      <path d={`M 0 ${height * 0.82} L ${width * lineEnd} ${height * 0.34}`} stroke="#e3f7fb" strokeWidth={height * 0.004} opacity={flicker} />
      <path d={`M ${width * 0.48} ${height * 0.06} C ${width * 0.55} ${height * 0.14}, ${width * 0.54} ${height * 0.28}, ${width * 0.51} ${height * 0.4} C ${width * 0.49} ${height * 0.5}, ${width * 0.54} ${height * 0.58}, ${width * 0.6} ${height * 0.65} L ${width * 0.72} ${height * 0.88} L ${width * 0.42} ${height * 0.88} C ${width * 0.47} ${height * 0.68}, ${width * 0.43} ${height * 0.54}, ${width * 0.44} ${height * 0.42} C ${width * 0.45} ${height * 0.27}, ${width * 0.42} ${height * 0.15}, ${width * 0.38} ${height * 0.06} Z`} fill="#0c0d0f" />
      <path d={`M ${width * 0.52} ${height * 0.38} l ${width * 0.1} ${height * 0.025} m ${-width * 0.08} ${height * 0.025} l ${width * 0.14} ${height * 0.026} m ${-width * 0.16} ${height * 0.028} l ${width * 0.12} ${height * 0.025}`} stroke="#d38b43" strokeWidth={3} opacity={0.2 + scrape * 0.35} />
    </svg>
    <div style={{position: 'absolute', left: '8%', top: '10%', fontSize: 22, letterSpacing: 4, color: '#8c979b'}}>THE PINCH POINT</div>
    <div style={{position: 'absolute', left: '8%', bottom: '10%', width: '44%', fontSize: 38, lineHeight: 1.1}}>Recovery is only real if it can pass the obstruction.</div>
    <div style={{position: 'absolute', right: '8%', bottom: '10%', fontFamily: 'Arial, sans-serif', fontSize: 18, letterSpacing: 2, color: '#8c979b'}}>{sourceLabel}</div>
  </AbsoluteFill>;
};

const Shot_m03: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.min(1, Math.max(0, progress));
  const reveal = interpolate(p, [0, 0.82, 1], [0, 1, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const railX = interpolate(p, [0, 1], [0.58, 0.84], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{backgroundColor: '#e8e1d4', overflow: 'hidden', fontFamily: 'Arial, sans-serif', color: '#20282b'}}>
    <div style={{position: 'absolute', left: '8%', right: '8%', top: '10%', bottom: '10%', backgroundColor: '#f5f0e8', border: '1px solid #c7c0b4', overflow: 'hidden'}}>
      {assetPath ? <Img src={staticFile(assetPath.replaceAll('\\','/'))} className={assetClass} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'contain', opacity: reveal}} /> : null}
      <div style={{position: 'absolute', inset: 0, backgroundColor: '#f5f0e8', opacity: 1 - reveal}} />
      <div style={{position: 'absolute', left: `${railX * 100}%`, top: '13%', bottom: '14%', width: 3, backgroundColor: '#d18a3f', boxShadow: '0 0 0 6px rgba(209,138,63,0.12)', opacity: reveal}} />
      <div style={{position: 'absolute', left: 24, top: 20, fontSize: 18, letterSpacing: 3, color: '#657176'}}>SUPPLIED WTI DATA</div>
      <div style={{position: 'absolute', right: 24, top: 20, fontSize: 16, letterSpacing: 2, color: '#657176'}}>{sourceLabel}</div>
    </div>
  </AbsoluteFill>;
};

const Shot_m04: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.min(1, Math.max(0, progress));
  const leftX = interpolate(p, [0, 0.72, 1], [0.18, 0.47, 0.52], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const rightX = interpolate(p, [0, 0.72, 1], [0.82, 0.53, 0.48], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const fade = interpolate(p, [0.56, 0.84, 1], [0, 0.2, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{backgroundColor: '#131d22', overflow: 'hidden', fontFamily: 'Georgia, serif', color: '#f2e7d2'}}>
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{position: 'absolute', inset: 0}}>
      <path d={`M ${width * 0.08} ${height * 0.68} L ${width * 0.92} ${height * 0.32}`} stroke="#36a8d5" strokeWidth={height * 0.14} opacity="0.17" />
      <path d={`M ${width * 0.08} ${height * 0.68} L ${width * 0.92} ${height * 0.32}`} stroke="#42b6dc" strokeWidth={height * 0.04} opacity="0.9" />
      <path d={`M ${width * 0.08} ${height * 0.68} L ${width * 0.92} ${height * 0.32}`} stroke="#d9f4fa" strokeWidth={height * 0.004} opacity="0.34" />
      <g opacity={fade}>
        <circle cx={width * leftX} cy={height * 0.68 - (leftX - 0.08) * height * 0.43} r={height * 0.027} fill="#d58c40" />
        <circle cx={width * rightX} cy={height * 0.68 - (rightX - 0.08) * height * 0.43} r={height * 0.027} fill="#d58c40" />
        <circle cx={width * leftX} cy={height * 0.68 - (leftX - 0.08) * height * 0.43} r={height * 0.065} fill="#d58c40" opacity="0.14" />
        <circle cx={width * rightX} cy={height * 0.68 - (rightX - 0.08) * height * 0.43} r={height * 0.065} fill="#d58c40" opacity="0.14" />
      </g>
    </svg>
    <div style={{position: 'absolute', left: '8%', top: '10%', fontSize: 22, letterSpacing: 4, color: '#8c979b'}}>REOPENING</div>
    <div style={{position: 'absolute', left: '8%', bottom: '10%', width: '52%', fontSize: 40, lineHeight: 1.08}}>The route works when movement runs both ways.</div>
    <div style={{position: 'absolute', right: '8%', bottom: '10%', fontFamily: 'Arial, sans-serif', fontSize: 18, letterSpacing: 2, color: '#8c979b'}}>{sourceLabel}</div>
  </AbsoluteFill>;
};

const Shot_m05: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.min(1, Math.max(0, progress));
  const typeOn = interpolate(p, [0.08, 0.72, 1], [0, 1, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const routeDrift = interpolate(p, [0, 1], [0, 0.07], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{backgroundColor: '#202326', overflow: 'hidden', fontFamily: 'Arial, sans-serif', color: '#eee6d7'}}>
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{position: 'absolute', inset: 0, opacity: 0.6}}>
      <path d={`M ${width * 0.06} ${height * (0.73 - routeDrift)} L ${width * 0.94} ${height * (0.25 - routeDrift)}`} stroke="#37acd8" strokeWidth={height * 0.025} opacity="0.6" />
      <path d={`M ${width * 0.06} ${height * (0.73 - routeDrift)} L ${width * 0.94} ${height * (0.25 - routeDrift)}`} stroke="#d18a3f" strokeWidth={height * 0.004} opacity="0.85" />
    </svg>
    <div style={{position: 'absolute', left: '8%', top: '10%', fontSize: 22, letterSpacing: 4, color: '#9ca5a8'}}>EVIDENCE NOTE</div>
    <div style={{position: 'absolute', left: '8%', top: '31%', width: '68%', borderLeft: '4px solid #d18a3f', paddingLeft: 26, clipPath: `inset(0 ${100 - typeOn * 100}% 0 0)`}}>
      <div style={{fontSize: 42, lineHeight: 1.08, fontFamily: 'Georgia, serif'}}>The EIA says</div>
      <div style={{marginTop: 24, fontSize: 25, lineHeight: 1.25, color: '#c9d1d0'}}>{sourceLabel}</div>
    </div>
    <div style={{position: 'absolute', left: '8%', bottom: '10%', fontSize: 18, letterSpacing: 2, color: '#9ca5a8'}}>SUPPLIED PRESS RELEASE / SOURCE MARK</div>
  </AbsoluteFill>;
};

const Shot_m06: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => { const p=Math.max(0,Math.min(1,progress)); const reveal=interpolate(p,[0,0.2],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.out(Easing.cubic)}); const needle=interpolate(p,[0.18,0.94],[18,76],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.cubic)}); const segments=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17]; return <AbsoluteFill style={{background:'radial-gradient(circle at 50% 46%, #182329 0%, #091114 53%, #05090b 100%)',color:'#f4ead4',overflow:'hidden',fontFamily:'Trebuchet MS, sans-serif'}}><svg viewBox='0 0 1600 900' style={{position:'absolute',inset:0,width:'100%',height:'100%'}}><defs><radialGradient id='m06Glow'><stop offset='0%' stopColor='#f6b94d' stopOpacity='0.2'/><stop offset='75%' stopColor='#f6b94d' stopOpacity='0.03'/><stop offset='100%' stopColor='#f6b94d' stopOpacity='0'/></radialGradient><clipPath id='m06Wipe'><circle cx='800' cy='430' r={360*reveal}/></clipPath></defs><circle cx='800' cy='430' r='355' fill='url(#m06Glow)'/><circle cx='800' cy='430' r='255' fill='#0a1215' stroke='#28353a' strokeWidth='2'/><g clipPath='url(#m06Wipe)'>{segments.map((i)=>{const threshold=i<7?0:0.12+(i-7)*0.065; const finalThreshold=i===17?0.92:threshold; const lit=i<7?1:interpolate(p,[finalThreshold,finalThreshold+0.09],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.out(Easing.cubic)}); return <line key={i} x1='800' y1='118' x2='800' y2='184' transform={`rotate(${i*20} 800 430)`} stroke={lit>0.5?'#f1aa3d':'#293237'} strokeWidth='28' strokeLinecap='round' opacity={0.38+lit*0.62}/>;})}</g><circle cx='800' cy='430' r='216' fill='none' stroke='#344248' strokeWidth='4'/><g transform={`rotate(${needle} 800 430)`}><line x1='800' y1='430' x2='800' y2='260' stroke='#f4b149' strokeWidth='8' strokeLinecap='round'/><circle cx='800' cy='430' r='17' fill='#f4b149'/></g><text x='800' y='440' textAnchor='middle' dominantBaseline='middle' fill='#f7ecd3' fontFamily='Georgia, serif' fontSize='46' letterSpacing='3'>GLOBAL OUTPUT</text><text x='800' y='500' textAnchor='middle' fill='#d1b77f' fontSize='25' letterSpacing='7'>YEAR-END GAUGE</text><path d='M510 705 H1090' stroke='#29373c' strokeWidth='2'/><circle cx='510' cy='705' r='5' fill='#f1aa3d'/><circle cx='1090' cy='705' r='5' fill={p>0.92?'#f1aa3d':'#293237'}/></svg>{sourceLabel?<div style={{position:'absolute',left:'8%',right:'8%',bottom:'4%',borderTop:'1px solid rgba(214,181,119,0.28)',paddingTop:10,textAlign:'right',fontSize:16,letterSpacing:2,color:'#a8997d',textTransform:'uppercase'}}>{sourceLabel}</div>:null}</AbsoluteFill>; };

const Shot_m07: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => { const p=Math.max(0,Math.min(1,progress)); const rows=[0,1,2,3]; const cols=[0,1,2,3,4,5]; const sweep=interpolate(p,[0.02,0.96],[-120,1640],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.cubic)}); return <AbsoluteFill style={{background:'linear-gradient(128deg, #071014 0%, #101b1e 54%, #071013 100%)',color:'#f2e7cf',overflow:'hidden',fontFamily:'Trebuchet MS, sans-serif'}}><svg viewBox='0 0 1600 900' style={{position:'absolute',inset:0,width:'100%',height:'100%'}}><defs><linearGradient id='m07Sweep' x1='0' x2='1'><stop offset='0%' stopColor='#f3ad42' stopOpacity='0'/><stop offset='50%' stopColor='#f3ad42' stopOpacity='0.18'/><stop offset='100%' stopColor='#f3ad42' stopOpacity='0'/></linearGradient></defs><text x='130' y='148' fill='#f5ead3' fontFamily='Georgia, serif' fontSize='44' letterSpacing='2'>RESTORATION GAUGE</text><text x='1470' y='148' textAnchor='end' fill='#d5b779' fontSize='25' letterSpacing='5'>Q1 2027</text><path d='M130 180 H1470' stroke='#354247' strokeWidth='2'/>{rows.map((r)=>cols.map((c)=>{const x=250+c*220; const y=288+r*124; const threshold=0.08+(r+c)*0.065; const on=interpolate(p,[threshold,threshold+0.12],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.out(Easing.cubic)}); const turn=interpolate(on,[0,1],[-40,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}); return <g key={`${r}-${c}`}><line x1={x-74} y1={y} x2={x+74} y2={y} stroke={on>0.45?'#9a7134':'#293439'} strokeWidth='12' strokeLinecap='round'/><circle cx={x} cy={y} r='28' fill='#10191c' stroke={on>0.45?'#efaa42':'#3a4448'} strokeWidth='6'/><g transform={`rotate(${turn} ${x} ${y})`}><path d={`M${x-20} ${y-20} L${x+20} ${y+20} M${x+20} ${y-20} L${x-20} ${y+20}`} stroke={on>0.45?'#ffc667':'#4a5356'} strokeWidth='7' strokeLinecap='round'/></g><circle cx={x} cy={y} r={7+on*4} fill={on>0.45?'#ffd17a':'#242d31'} opacity={0.55+on*0.45}/></g>;}))}<rect x={sweep-170} y='204' width='340' height='560' fill='url(#m07Sweep)' transform='skewX(-10)'/><path d='M130 795 H1470' stroke='#273438' strokeWidth='2'/><text x='130' y='835' fill='#8e9b9c' fontSize='18' letterSpacing='4'>STAGGERED RESTART</text></svg>{sourceLabel?<div style={{position:'absolute',left:'8%',right:'8%',bottom:'4%',borderTop:'1px solid rgba(214,181,119,0.28)',paddingTop:10,textAlign:'right',fontSize:16,letterSpacing:2,color:'#a8997d',textTransform:'uppercase'}}>{sourceLabel}</div>:null}</AbsoluteFill>; };

const Shot_m08: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => { const p=Math.max(0,Math.min(1,progress)); const move=interpolate(p,[0.03,0.94],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.cubic)}); const q3x=250-move*910; const q1x=1220-move*470; const markerSettle=spring({frame:frame-4,fps,config:{damping:18,stiffness:150,mass:0.8}}); return <AbsoluteFill style={{background:'linear-gradient(115deg, #0a1215 0%, #172126 48%, #090f12 100%)',color:'#f4e8d0',overflow:'hidden',fontFamily:'Trebuchet MS, sans-serif'}}><svg viewBox='0 0 1600 900' style={{position:'absolute',inset:0,width:'100%',height:'100%'}}><defs><linearGradient id='m08Paper' x1='0' y1='0' x2='0' y2='1'><stop offset='0%' stopColor='#eee5d1'/><stop offset='100%' stopColor='#cfc3aa'/></linearGradient><filter id='m08Shadow' x='-30%' y='-30%' width='160%' height='160%'><feDropShadow dx='0' dy='22' stdDeviation='18' floodColor='#000' floodOpacity='0.35'/></filter></defs><text x='130' y='145' fill='#ddcda9' fontSize='22' letterSpacing='7'>FORECAST WINDOW</text><path d='M130 180 H1470' stroke='#364349' strokeWidth='2'/><g transform={`translate(${q3x} 250)`} filter='url(#m08Shadow)'><path d='M0 0 H680 L730 50 V430 H0 Z' fill='url(#m08Paper)'/><path d='M680 0 V50 H730' fill='none' stroke='#b4a78e' strokeWidth='3'/><rect x='0' y='0' width='730' height='76' fill='#2d383b'/><text x='54' y='53' fill='#d9cba9' fontSize='21' letterSpacing='5'>CALENDAR</text><text x='365' y='245' textAnchor='middle' fill='#1b2426' fontFamily='Georgia, serif' fontSize='82'>Q3 2026</text><path d='M75 318 H655' stroke='#aaa088' strokeWidth='2'/></g><g transform={`translate(${q1x} 250)`} filter='url(#m08Shadow)'><path d='M0 0 H680 L730 50 V430 H0 Z' fill='url(#m08Paper)'/><path d='M680 0 V50 H730' fill='none' stroke='#b4a78e' strokeWidth='3'/><rect x='0' y='0' width='730' height='76' fill='#263135'/><text x='54' y='53' fill='#d9cba9' fontSize='21' letterSpacing='5'>CALENDAR</text><text x='365' y='245' textAnchor='middle' fill='#172123' fontFamily='Georgia, serif' fontSize='82'>Q1 2027</text><path d='M75 318 H655' stroke='#aaa088' strokeWidth='2'/></g><g opacity={markerSettle} transform={`translate(0 ${interpolate(markerSettle,[0,1],[-34,0])})`}><line x1='800' y1='208' x2='800' y2='733' stroke='#f0aa3f' strokeWidth='8'/><path d='M800 178 L827 208 L800 238 L773 208 Z' fill='#ffc35e'/><rect x='680' y='720' width='240' height='64' rx='32' fill='#efaa40'/><text x='800' y='761' textAnchor='middle' fill='#172023' fontSize='22' fontWeight='700' letterSpacing='4'>RESTORED</text></g></svg>{sourceLabel?<div style={{position:'absolute',left:'8%',right:'8%',bottom:'4%',borderTop:'1px solid rgba(214,181,119,0.28)',paddingTop:10,textAlign:'right',fontSize:16,letterSpacing:2,color:'#a8997d',textTransform:'uppercase'}}>{sourceLabel}</div>:null}</AbsoluteFill>; };

const Shot_m09: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => { const p=Math.max(0,Math.min(1,progress)); const lanes=[{label:'TRANSIT',y:300,dir:-1},{label:'PRODUCTION',y:470,dir:1},{label:'INVENTORIES',y:640,dir:-1}]; const flow=interpolate(p,[0.16,0.66,1],[0,1,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.out(Easing.cubic)}); return <AbsoluteFill style={{background:'linear-gradient(145deg, #071013 0%, #111b1f 52%, #060b0d 100%)',color:'#f4ead4',overflow:'hidden',fontFamily:'Trebuchet MS, sans-serif'}}><svg viewBox='0 0 1600 900' style={{position:'absolute',inset:0,width:'100%',height:'100%'}}><defs><linearGradient id='m09Flow' x1='0' x2='1'><stop offset='0%' stopColor='#9b682a'/><stop offset='72%' stopColor='#efaa40'/><stop offset='100%' stopColor='#ffd47c'/></linearGradient></defs><text x='130' y='135' fill='#f2e6ce' fontFamily='Georgia, serif' fontSize='43'>THE MARKET MECHANISM</text><text x='1470' y='135' textAnchor='end' fill='#879698' fontSize='19' letterSpacing='5'>THREE-LANE TEST</text><path d='M130 172 H1470' stroke='#344247' strokeWidth='2'/>{lanes.map((lane,i)=>{const enter=interpolate(p,[i*0.08,0.24+i*0.08],[lane.dir*1500,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.out(Easing.cubic)}); return <g key={lane.label} transform={`translate(${enter} 0)`}><text x='145' y={lane.y+9} fill={i===0?'#e4c487':'#9aa6a7'} fontSize='24' fontWeight='700' letterSpacing='4'>{lane.label}</text><line x1='400' y1={lane.y} x2='1420' y2={lane.y} stroke='#324044' strokeWidth='38' strokeLinecap='round'/><line x1='400' y1={lane.y} x2='1420' y2={lane.y} stroke='#10191c' strokeWidth='24' strokeLinecap='round'/><circle cx='400' cy={lane.y} r='27' fill='#0b1316' stroke='#48575a' strokeWidth='5'/><circle cx='1420' cy={lane.y} r='27' fill='#0b1316' stroke='#48575a' strokeWidth='5'/></g>;})}<line x1='400' y1='300' x2={400+760*flow} y2='300' stroke='url(#m09Flow)' strokeWidth='18' strokeLinecap='round'/><circle cx={400+760*flow} cy='300' r={13+5*interpolate(p,[0,0.5,1],[0,1,0])} fill='#ffd078'/><g opacity={interpolate(p,[0.64,0.78],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})}><line x1='1200' y1='260' x2='1200' y2='340' stroke='#d99a3d' strokeWidth='5'/><text x='1230' y='309' fill='#d6bd8a' fontSize='21' letterSpacing='3'>PAUSE</text></g><path d='M130 770 H1470' stroke='#273438' strokeWidth='2'/></svg>{sourceLabel?<div style={{position:'absolute',left:'8%',right:'8%',bottom:'4%',borderTop:'1px solid rgba(214,181,119,0.28)',paddingTop:10,textAlign:'right',fontSize:16,letterSpacing:2,color:'#a8997d',textTransform:'uppercase'}}>{sourceLabel}</div>:null}</AbsoluteFill>; };

const Shot_m10: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => { const p=Math.max(0,Math.min(1,progress)); const marks=[{x:520,delay:0},{x:790,delay:0.11},{x:1060,delay:0.22}]; const clear=interpolate(p,[0.46,0.9],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.out(Easing.cubic)}); return <AbsoluteFill style={{background:'radial-gradient(circle at 50% 52%, #172226 0%, #091114 58%, #05090b 100%)',color:'#f4ead4',overflow:'hidden',fontFamily:'Trebuchet MS, sans-serif'}}><svg viewBox='0 0 1600 900' style={{position:'absolute',inset:0,width:'100%',height:'100%'}}><defs><linearGradient id='m10Lane' x1='0' x2='1'><stop offset='0%' stopColor='#725027'/><stop offset='55%' stopColor='#e4a03b'/><stop offset='100%' stopColor='#ffca69'/></linearGradient><linearGradient id='m10Tape' x1='0' y1='0' x2='1' y2='1'><stop offset='0%' stopColor='#c84635'/><stop offset='50%' stopColor='#8e211c'/><stop offset='100%' stopColor='#d85842'/></linearGradient></defs><text x='130' y='142' fill='#e5d8bd' fontSize='22' letterSpacing='7'>PHASE ONE</text><text x='1470' y='142' textAnchor='end' fill='#c35b49' fontSize='22' letterSpacing='6'>DISRUPTION</text><path d='M130 178 H1470' stroke='#344247' strokeWidth='2'/><text x='130' y='397' fill='#d7bf8c' fontSize='28' fontWeight='700' letterSpacing='5'>TRANSIT</text><line x1='360' y1='390' x2='1430' y2='390' stroke='#364448' strokeWidth='70' strokeLinecap='round'/><line x1='360' y1='390' x2='1430' y2='390' stroke='#0d171a' strokeWidth='48' strokeLinecap='round'/><line x1='360' y1='390' x2={360+1070*clear} y2='390' stroke='url(#m10Lane)' strokeWidth='22' strokeLinecap='round'/><circle cx='360' cy='390' r='35' fill='#0a1316' stroke='#596669' strokeWidth='7'/><circle cx='1430' cy='390' r='35' fill='#0a1316' stroke={clear>0.92?'#e6a33f':'#596669'} strokeWidth='7'/>{marks.map((mark,i)=>{const peel=interpolate(p,[0.12+mark.delay,0.58+mark.delay],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.in(Easing.cubic)}); const lift=interpolate(peel,[0,1],[0,-310]); const rotate=interpolate(peel,[0,1],[0,i%2===0?-38:42]); const curl=interpolate(peel,[0,1],[1,0.72]); return <g key={i} transform={`translate(0 ${lift}) rotate(${rotate} ${mark.x} 390) scale(1 ${curl})`} opacity={1-interpolate(peel,[0.72,1],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})}><rect x={mark.x-42} y='280' width='84' height='220' rx='8' fill='url(#m10Tape)' transform={`rotate(${i%2===0?-34:34} ${mark.x} 390)`}/><path d={`M${mark.x-20} 292 L${mark.x+18} 487`} stroke='#f18b73' strokeWidth='5' opacity='0.55' transform={`rotate(${i%2===0?-34:34} ${mark.x} 390)`}/></g>;})}<g opacity={interpolate(p,[0.66,0.92],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})}><path d='M360 584 H1430' stroke='#334145' strokeWidth='2'/><text x='895' y='650' textAnchor='middle' fill='#e8d7b5' fontFamily='Georgia, serif' fontSize='46'>THE LANE CLEARS</text><path d='M790 700 H1000' stroke='#e6a33f' strokeWidth='6' strokeLinecap='round'/><path d='M1000 700 L974 683 V717 Z' fill='#e6a33f'/></g></svg>{sourceLabel?<div style={{position:'absolute',left:'8%',right:'8%',bottom:'4%',borderTop:'1px solid rgba(214,181,119,0.28)',paddingTop:10,textAlign:'right',fontSize:16,letterSpacing:2,color:'#a8997d',textTransform:'uppercase'}}>{sourceLabel}</div>:null}</AbsoluteFill>; };

const Shot_m11: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.max(0, Math.min(1, progress));
  const ease = Easing.bezier(0.22, 0.8, 0.24, 1);
  const flow = interpolate(ease(p), [0, 1], [0.18, 0.9]);
  const valve = interpolate(ease(p), [0, 1], [0, 1]);
  const valveAngle = interpolate(valve, [0, 1], [-42, 0]);
  const pulse = interpolate(Math.sin(frame / (fps * 0.28)), [-1, 1], [0.9, 1.1]);
  const laneY = height * 0.56;
  const chrome = { position: 'absolute' as const, left: '8%', right: '8%', top: '10%', bottom: '10%' };
  return <AbsoluteFill style={{backgroundColor:'#101313',color:'#F3E8D0',fontFamily:'Georgia, serif'}}>
    <div style={chrome}>
      <div style={{position:'absolute',top:0,left:0,fontFamily:'Arial, sans-serif',fontSize:13,letterSpacing:3,color:'#C99A47'}}>PHASE 02 / NORMALIZATION</div>
      {sourceLabel ? <div style={{position:'absolute',top:0,right:0,fontFamily:'Arial, sans-serif',fontSize:11,letterSpacing:1.5,color:'#A9AAA0'}}>{sourceLabel}</div> : null}
      <div style={{position:'absolute',left:0,right:0,top:'42%',height:5,background:'#35403C',borderRadius:4}}>
        <div style={{position:'absolute',left:0,top:-3,height:11,width:`${flow*100}%`,background:'#D89A38',borderRadius:8,boxShadow:'0 0 22px rgba(216,154,56,.45)',transform:`scaleY(${pulse})`,transformOrigin:'left center'}} />
      </div>
      <div style={{position:'absolute',left:0,top:laneY-48,fontFamily:'Arial, sans-serif',fontSize:14,letterSpacing:2,color:'#8F968B'}}>PRODUCTION</div>
      <div style={{position:'absolute',right:0,top:laneY-48,fontFamily:'Arial, sans-serif',fontSize:12,letterSpacing:2,color:'#6F766F'}}>FLOW WIDENS</div>
      {[0.28,0.52,0.76].map((x,i) => <div key={i} style={{position:'absolute',left:`${x*100}%`,top:laneY-18,width:34,height:34,border:'2px solid #D89A38',borderRadius:'50%',background:'#101313',transform:`translateX(-50%) rotate(${valveAngle}deg)`}}><div style={{position:'absolute',left:15,top:-9,width:2,height:50,background:'#D89A38',transform:`rotate(${i%2 ? -45 : 45}deg)`,transformOrigin:'center'}} /></div>)}
      <div style={{position:'absolute',left:0,right:0,top:'67%',height:1,background:'#27302C'}} />
      <div style={{position:'absolute',left:0,top:'72%',fontSize:30,letterSpacing:-.5}}>The next phase is about normalization.</div>
    </div>
  </AbsoluteFill>;
};

const Shot_m12: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.max(0, Math.min(1, progress));
  const ease = Easing.bezier(0.18, 0.72, 0.25, 1);
  const drop = interpolate(ease(p), [0, 0.32, 1], [0, 1, 1]);
  const ripple = interpolate(ease(Math.max(0, (p - 0.22) / 0.78)), [0, 1], [0.06, 1]);
  const water = interpolate(ease(p), [0, 1], [0.02, 0.16]);
  const cx = width * 0.5;
  const cy = height * 0.53;
  return <AbsoluteFill style={{backgroundColor:'#D8D0BC',color:'#202B29',fontFamily:'Georgia, serif'}}>
    <div style={{position:'absolute',left:'8%',right:'8%',top:'10%',bottom:'10%'}}>
      <div style={{position:'absolute',top:0,left:0,fontFamily:'Arial, sans-serif',fontSize:13,letterSpacing:3,color:'#63736A'}}>MARKET TEST / INVENTORY</div>
      {sourceLabel ? <div style={{position:'absolute',top:0,right:0,fontFamily:'Arial, sans-serif',fontSize:11,letterSpacing:1.5,color:'#63736A'}}>{sourceLabel}</div> : null}
      <svg width={width*0.84} height={height*0.72} viewBox={`0 0 ${width} ${height}`} style={{position:'absolute',left:'-2%',top:'9%'}}>
        <ellipse cx={cx} cy={cy+22} rx={width*.27} ry={height*.19} fill="#C4B89C" opacity=".8" />
        <ellipse cx={cx} cy={cy} rx={width*.27} ry={height*.19} fill="#B6AA90" stroke="#5C685D" strokeWidth="2" />
        <ellipse cx={cx} cy={cy-5} rx={width*.205} ry={height*.13} fill={`rgba(53,92,84,${water})`} stroke="#7D856F" strokeWidth="2" />
        {[0,1,2,3].map(i => <ellipse key={i} cx={cx} cy={cy-5} rx={width*(.075+i*.045)*ripple} ry={height*(.035+i*.022)*ripple} fill="none" stroke="#E9D9B2" strokeWidth="2" opacity={.76-i*.13} />)}
        <circle cx={cx} cy={cy-110*drop} r="7" fill="#D89A38" opacity={drop} />
        <line x1={cx} y1={cy-145*drop} x2={cx} y2={cy-8} stroke="#D89A38" strokeWidth="3" opacity={drop*.7} />
      </svg>
      <div style={{position:'absolute',left:0,right:0,bottom:'2%',textAlign:'center',fontFamily:'Arial, sans-serif',fontSize:14,letterSpacing:3,color:'#63736A'}}>INVENTORY / LOW LEVEL</div>
      <div style={{position:'absolute',left:0,right:0,top:'89%',textAlign:'center',fontSize:29}}>Do inventories rebuild?</div>
    </div>
  </AbsoluteFill>;
};

const Shot_m13: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.max(0, Math.min(1, progress));
  const settle = spring({frame:frame, fps:fps, config:{damping:16, stiffness:80, mass:0.7}});
  const needle = Math.sin(frame / (fps * 0.32)) * 19 * (1 - p*.15);
  const incoming = interpolate(Easing.bezier(0.3,0.8,0.25,1)(p), [0,1], [0.18,0.72]);
  const centerX = width * .5;
  const centerY = height * .52;
  return <AbsoluteFill style={{backgroundColor:'#121719',color:'#F1E5CE',fontFamily:'Georgia, serif'}}>
    <div style={{position:'absolute',left:'8%',right:'8%',top:'10%',bottom:'10%'}}>
      <div style={{position:'absolute',top:0,left:0,fontFamily:'Arial, sans-serif',fontSize:13,letterSpacing:3,color:'#D89A38'}}>MARKET TEST / DEMAND</div>
      {sourceLabel ? <div style={{position:'absolute',top:0,right:0,fontFamily:'Arial, sans-serif',fontSize:11,letterSpacing:1.5,color:'#9DA49A'}}>{sourceLabel}</div> : null}
      <svg width={width*.84} height={height*.7} viewBox={`0 0 ${width} ${height}`} style={{position:'absolute',left:'-2%',top:'10%'}}>
        <line x1={width*.09} y1={centerY} x2={width*.37} y2={centerY} stroke="#D89A38" strokeWidth="9" strokeLinecap="round" opacity={incoming} />
        <polygon points={`${width*.37},${centerY-14} ${width*.37},${centerY+14} ${width*.42},${centerY}`} fill="#D89A38" opacity={incoming} />
        <line x1={width*.63} y1={centerY} x2={width*.91} y2={centerY} stroke="#A8B2A6" strokeWidth="9" strokeLinecap="round" opacity=".9" />
        <polygon points={`${width*.63},${centerY-14} ${width*.63},${centerY+14} ${width*.58},${centerY}`} fill="#A8B2A6" />
        <circle cx={centerX} cy={centerY} r={width*.145} fill="#1C2524" stroke="#D8C49B" strokeWidth="3" />
        <circle cx={centerX} cy={centerY} r={width*.11} fill="none" stroke="#52615A" strokeWidth="2" strokeDasharray="4 9" />
        <line x1={centerX} y1={centerY} x2={centerX + Math.sin((needle+settle*4)*Math.PI/180)*width*.095} y2={centerY - Math.cos((needle+settle*4)*Math.PI/180)*width*.095} stroke="#E2A342" strokeWidth="5" strokeLinecap="round" />
        <circle cx={centerX} cy={centerY} r="8" fill="#E2A342" />
      </svg>
      <div style={{position:'absolute',left:'9%',top:'54%',fontFamily:'Arial, sans-serif',fontSize:14,letterSpacing:2,color:'#D89A38'}}>SUPPLY</div>
      <div style={{position:'absolute',right:'9%',top:'54%',fontFamily:'Arial, sans-serif',fontSize:14,letterSpacing:2,color:'#A8B2A6'}}>DEMAND</div>
      <div style={{position:'absolute',left:0,right:0,bottom:'2%',textAlign:'center',fontSize:29}}>And does demand absorb the recovery?</div>
    </div>
  </AbsoluteFill>;
};

const Shot_m14: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.max(0, Math.min(1, progress));
  const track = interpolate(Easing.bezier(0.2,0.75,0.25,1)(p), [0,1], [0, 38]);
  const src = assetPath ? staticFile(assetPath.replaceAll('\\','/')) : undefined;
  return <AbsoluteFill style={{backgroundColor:'#0E1213',color:'#F2E8D3',fontFamily:'Georgia, serif'}}>
    <div style={{position:'absolute',left:'8%',right:'8%',top:'10%',bottom:'10%'}}>
      {sourceLabel ? <div style={{position:'absolute',top:0,right:0,zIndex:3,fontFamily:'Arial, sans-serif',fontSize:11,letterSpacing:1.5,color:'#A7AAA0'}}>{sourceLabel}</div> : null}
      <div style={{position:'absolute',top:0,left:0,fontFamily:'Arial, sans-serif',fontSize:13,letterSpacing:3,color:'#C99A47'}}>SUPPLIED DATA / RECENT PRICE PATH</div>
      <div style={{position:'absolute',left:0,right:0,top:'17%',height:'62%',overflow:'hidden',borderTop:'1px solid #59635C',borderBottom:'1px solid #59635C'}}>
        {src ? <Img src={src} style={{position:'absolute',left:`-${track}%`,top:0,width:'138%',height:'100%',objectFit:'cover',objectPosition:'center'}} /> : <svg width="100%" height="100%" viewBox="0 0 1000 360" preserveAspectRatio="none"><polyline points="0,255 100,220 190,245 280,155 365,190 455,120 540,145 625,85 720,130 820,72 1000,102" fill="none" stroke="#D89A38" strokeWidth="5" /></svg>}
        <div style={{position:'absolute',right:0,top:0,bottom:0,width:'31%',borderLeft:'2px solid #F0D9A0',background:'linear-gradient(90deg, transparent, rgba(14,18,19,.18))'}} />
      </div>
      <div style={{position:'absolute',left:0,bottom:'7%',fontSize:27}}>The price path in the supplied WTI data gives the story a market backdrop.</div>
    </div>
  </AbsoluteFill>;
};

const Shot_m15: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.max(0, Math.min(1, progress));
  const reveal = interpolate(Easing.bezier(0.18,0.8,0.22,1)(p), [0,1], [0,1]);
  const src = assetPath ? staticFile(assetPath.replaceAll('\\','/')) : undefined;
  return <AbsoluteFill style={{backgroundColor:'#E6DDC9',color:'#202B29',fontFamily:'Georgia, serif'}}>
    <div style={{position:'absolute',left:'8%',right:'8%',top:'10%',bottom:'10%'}}>
      <div style={{position:'absolute',top:0,left:0,fontFamily:'Arial, sans-serif',fontSize:13,letterSpacing:3,color:'#63736A'}}>OBSERVED → OUTLOOK</div>
      {sourceLabel ? <div style={{position:'absolute',top:0,right:0,fontFamily:'Arial, sans-serif',fontSize:11,letterSpacing:1.5,color:'#63736A'}}>{sourceLabel}</div> : null}
      <div style={{position:'absolute',left:0,top:'18%',width:'46%',height:'58%',overflow:'hidden',borderRight:'1px solid #879084'}}>
        {src ? <Img src={src} style={{width:'100%',height:'100%',objectFit:'cover',objectPosition:'center'}} /> : <svg width="100%" height="100%" viewBox="0 0 500 330" preserveAspectRatio="none"><polyline points="0,245 70,210 135,225 200,160 275,190 350,115 420,135 500,90" fill="none" stroke="#55655D" strokeWidth="5" /></svg>}
      </div>
      <div style={{position:'absolute',left:'52%',right:0,top:'18%',height:'58%',border: '2px dashed #879084',background:'rgba(255,250,235,.3)',overflow:'hidden'}}>
        <div style={{position:'absolute',left:0,top:'58%',width:`${reveal*100}%`,height:4,background:'#D89A38',transform:'rotate(-8deg)',transformOrigin:'left center'}} />
        <div style={{position:'absolute',left:`${reveal*70}%`,top:'42%',width:12,height:12,borderRadius:'50%',background:'#D89A38',opacity:reveal}} />
        <div style={{position:'absolute',left:18,top:16,fontFamily:'Arial, sans-serif',fontSize:12,letterSpacing:2,color:'#7A8177'}}>FORECAST CORRIDOR</div>
      </div>
      <div style={{position:'absolute',left:0,top:'79%',fontFamily:'Arial, sans-serif',fontSize:12,letterSpacing:2,color:'#63736A'}}>MULTI-YEAR RANGE</div>
      <div style={{position:'absolute',left:'52%',top:'79%',fontFamily:'Arial, sans-serif',fontSize:12,letterSpacing:2,color:'#63736A'}}>BLANK UNTIL OUTLOOK</div>
      <div style={{position:'absolute',left:0,right:0,bottom:'1%',fontSize:27}}>The forward-looking numbers come from the EIA's outlook.</div>
    </div>
  </AbsoluteFill>;
};

const Shot_m16: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.max(0, Math.min(1, progress));
  const drop = interpolate(p, [0, 0.62, 1], [-92, 0, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const settle = interpolate(p, [0.62, 0.82, 1], [0, 1, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const markerY = 238 + drop;
  const pulse = interpolate(p, [0.78, 0.9, 1], [0, 1, 0.45], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const bg = '#071c27';
  const amber = '#f2ac45';
  const pale = '#e9dfc8';
  return <AbsoluteFill style={{backgroundColor:bg, color:pale, fontFamily:'Georgia, serif', overflow:'hidden'}}>
    <svg width={width} height={height} viewBox="0 0 1600 900" style={{position:'absolute', inset:0}}>
      <defs>
        <linearGradient id="m16bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#0b2b38"/><stop offset="1" stopColor="#061720"/></linearGradient>
        <filter id="m16glow"><feGaussianBlur stdDeviation="12"/></filter>
      </defs>
      <rect width="1600" height="900" fill="url(#m16bg)"/>
      <path d="M176 706 C390 584 592 610 790 468 C950 353 1112 390 1406 220" fill="none" stroke="#244452" strokeWidth="3"/>
      <path d="M176 706 C390 584 592 610 790 468 C950 353 1112 390 1406 220" fill="none" stroke={amber} strokeOpacity="0.16" strokeWidth="18" filter="url(#m16glow)"/>
      <line x1="190" y1="180" x2="1410" y2="180" stroke="#47707a" strokeWidth="2" strokeDasharray="8 18"/>
      <line x1="190" y1="706" x2="1410" y2="706" stroke="#47707a" strokeWidth="2"/>
      <text x="190" y="142" fill="#7fa1a6" fontSize="26" letterSpacing="7">FORECAST CORRIDOR</text>
      <text x="190" y="258" fill={amber} fontSize="54" fontWeight="700" letterSpacing="5">JUNE</text>
      <text x="1408" y="752" textAnchor="end" fill="#7fa1a6" fontSize="22" letterSpacing="4">USD / BARREL</text>
      <circle cx="790" cy={markerY} r={38 + pulse * 14} fill={amber} opacity={0.12 + pulse * 0.12}/>
      <circle cx="790" cy={markerY} r="19" fill={amber} opacity={settle}/>
      <line x1="790" y1={markerY + 28} x2="790" y2="706" stroke={amber} strokeWidth="2" opacity={settle * 0.75}/>
      <text x="836" y={markerY + 18} fill={pale} fontSize="94" fontWeight="700">85</text>
      <text x="842" y={markerY + 55} fill="#9eb4b0" fontSize="24" letterSpacing="3">AVERAGE</text>
    </svg>
    <div style={{position:'absolute',left:'8%',right:'8%',top:'10%',height:34,display:'flex',justifyContent:'space-between',alignItems:'center',fontFamily:'Arial, sans-serif',fontSize:14,letterSpacing:3,color:'#8aa5a7'}}><span>BRENT OUTLOOK</span>{sourceLabel ? <span>{sourceLabel}</span> : null}</div>
  </AbsoluteFill>;
};

const Shot_m17: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.max(0, Math.min(1, progress));
  const draw = interpolate(p, [0, 0.72, 1], [0, 1, 1], {extrapolateLeft:'clamp', extrapolateRight:'clamp'});
  const lock = interpolate(p, [0.68, 0.86, 1], [0, 1, 1], {extrapolateLeft:'clamp', extrapolateRight:'clamp'});
  const path = 'M210 280 C430 280 530 330 720 410 S1020 570 1370 650';
  const markerX = interpolate(p, [0.72, 1], [1030, 1125], {extrapolateLeft:'clamp', extrapolateRight:'clamp'});
  const markerY = interpolate(p, [0.72, 1], [571, 591], {extrapolateLeft:'clamp', extrapolateRight:'clamp'});
  return <AbsoluteFill style={{backgroundColor:'#071c27', color:'#e9dfc8', fontFamily:'Georgia, serif', overflow:'hidden'}}>
    <svg width={width} height={height} viewBox="0 0 1600 900" style={{position:'absolute',inset:0}}>
      <rect width="1600" height="900" fill="#071c27"/>
      <path d="M190 690 H1410" stroke="#34535b" strokeWidth="2"/>
      <path d="M190 180 H1410" stroke="#34535b" strokeWidth="2" strokeDasharray="7 17"/>
      <path d={path} fill="none" stroke="#f2ac45" strokeWidth="7" strokeLinecap="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1-draw}/>
      <path d={path} fill="none" stroke="#f2ac45" strokeOpacity="0.13" strokeWidth="24" pathLength="1" strokeDasharray="1" strokeDashoffset={1-draw}/>
      <text x="190" y="136" fill="#7fa1a6" fontFamily="Arial, sans-serif" fontSize="25" letterSpacing="6">FORECAST CORRIDOR</text>
      <text x="190" y="754" fill="#9eb4b0" fontFamily="Arial, sans-serif" fontSize="24" letterSpacing="4">JUNE</text>
      <text x="1410" y="754" textAnchor="end" fill="#9eb4b0" fontFamily="Arial, sans-serif" fontSize="24" letterSpacing="4">Q3 2026</text>
      <circle cx={markerX} cy={markerY} r="26" fill="#f2ac45" opacity={lock}/>
      <line x1={markerX} y1={markerY+37} x2={markerX} y2="690" stroke="#f2ac45" strokeWidth="2" opacity={lock * 0.75}/>
      <text x={markerX+40} y={markerY+16} fill="#e9dfc8" fontSize="94" fontWeight="700" opacity={lock}>74</text>
    </svg>
    <div style={{position:'absolute',left:'8%',right:'8%',top:'10%',height:34,display:'flex',justifyContent:'space-between',alignItems:'center',fontFamily:'Arial, sans-serif',fontSize:14,letterSpacing:3,color:'#8aa5a7'}}><span>BRENT OUTLOOK</span>{sourceLabel ? <span>{sourceLabel}</span> : null}</div>
  </AbsoluteFill>;
};

const Shot_m18: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.max(0, Math.min(1, progress));
  const draw = interpolate(p, [0, 0.68, 1], [0, 1, 1], {extrapolateLeft:'clamp', extrapolateRight:'clamp'});
  const slow = interpolate(p, [0.58, 0.82, 1], [0, 1, 1], {extrapolateLeft:'clamp', extrapolateRight:'clamp'});
  const glow = interpolate(p, [0.8, 0.93, 1], [0, 1, 0.35], {extrapolateLeft:'clamp', extrapolateRight:'clamp'});
  const path = 'M190 236 C405 250 560 315 730 405 C890 490 1010 555 1124 612 C1210 653 1312 668 1410 682';
  return <AbsoluteFill style={{backgroundColor:'#071c27', color:'#e9dfc8', fontFamily:'Georgia, serif', overflow:'hidden'}}>
    <svg width={width} height={height} viewBox="0 0 1600 900" style={{position:'absolute',inset:0}}>
      <defs><filter id="m18glow"><feGaussianBlur stdDeviation="15"/></filter></defs>
      <rect width="1600" height="900" fill="#071c27"/>
      <path d="M170 714 C430 668 610 714 820 690 S1190 700 1430 730" fill="none" stroke="#244452" strokeWidth="18"/>
      <path d="M170 714 C430 668 610 714 820 690 S1190 700 1430 730" fill="none" stroke="#f2ac45" strokeOpacity="0.2" strokeWidth="4"/>
      <path d={path} fill="none" stroke="#f2ac45" strokeWidth="7" strokeLinecap="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1-draw}/>
      <path d={path} fill="none" stroke="#f2ac45" strokeOpacity="0.18" strokeWidth="26" filter="url(#m18glow)" pathLength="1" strokeDasharray="1" strokeDashoffset={1-draw}/>
      <text x="190" y="142" fill="#7fa1a6" fontFamily="Arial, sans-serif" fontSize="25" letterSpacing="6">BRENT OUTLOOK</text>
      <text x="1410" y="754" textAnchor="end" fill="#9eb4b0" fontFamily="Arial, sans-serif" fontSize="24" letterSpacing="4">2027</text>
      <circle cx="1410" cy="682" r={34 + glow*18} fill="#f2ac45" opacity={0.1 + glow*0.15}/>
      <circle cx="1410" cy="682" r="25" fill="#f2ac45" opacity={slow}/>
      <text x="1304" y="604" fill="#e9dfc8" fontSize="94" fontWeight="700" opacity={slow}>65</text>
      <text x="1308" y="640" fill="#9eb4b0" fontFamily="Arial, sans-serif" fontSize="22" letterSpacing="3" opacity={slow}>USD / BARREL</text>
    </svg>
    <div style={{position:'absolute',left:'8%',right:'8%',top:'10%',height:34,display:'flex',justifyContent:'space-between',alignItems:'center',fontFamily:'Arial, sans-serif',fontSize:14,letterSpacing:3,color:'#8aa5a7'}}><span>FORECAST PATH</span>{sourceLabel ? <span>{sourceLabel}</span> : null}</div>
  </AbsoluteFill>;
};

const Shot_m19: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.max(0, Math.min(1, progress));
  const leftFill = interpolate(p, [0, 0.72, 1], [0, 0.82, 0.82], {extrapolateLeft:'clamp', extrapolateRight:'clamp'});
  const rightFill = interpolate(p, [0, 0.78, 1], [0, 0.63, 0.63], {extrapolateLeft:'clamp', extrapolateRight:'clamp'});
  return <AbsoluteFill style={{backgroundColor:'#071c27', color:'#e9dfc8', fontFamily:'Georgia, serif', overflow:'hidden'}}>
    <svg width={width} height={height} viewBox="0 0 1600 900" style={{position:'absolute',inset:0}}>
      <rect width="1600" height="900" fill="#071c27"/>
      <text x="190" y="140" fill="#7fa1a6" fontFamily="Arial, sans-serif" fontSize="25" letterSpacing="6">GASOLINE FORECAST</text>
      <line x1="800" y1="210" x2="800" y2="760" stroke="#c98f3b" strokeOpacity="0.65" strokeWidth="2"/>
      <g transform="translate(285 220)">
        <path d="M48 470 V88 Q48 42 94 42 H245 Q291 42 291 88 V470" fill="none" stroke="#d8d0bd" strokeWidth="12"/>
        <rect x="80" y={470-320*leftFill} width="179" height={320*leftFill} fill="#f2ac45" opacity="0.9"/>
        <rect x="80" y="150" width="179" height="320" fill="none" stroke="#54717a" strokeWidth="3"/>
        <path d="M291 116 H350 V330 Q350 382 304 382" fill="none" stroke="#d8d0bd" strokeWidth="10"/>
        <circle cx="169" cy="104" r="25" fill="#071c27" stroke="#d8d0bd" strokeWidth="7"/>
        <text x="169" y="570" textAnchor="middle" fill="#e9dfc8" fontSize="78" fontWeight="700">3.80</text>
        <text x="169" y="612" textAnchor="middle" fill="#9eb4b0" fontFamily="Arial, sans-serif" fontSize="23" letterSpacing="4">Q3 2026</text>
      </g>
      <g transform="translate(940 220)">
        <path d="M48 470 V88 Q48 42 94 42 H245 Q291 42 291 88 V470" fill="none" stroke="#d8d0bd" strokeWidth="12"/>
        <rect x="80" y={470-320*rightFill} width="179" height={320*rightFill} fill="#d18138" opacity="0.88"/>
        <rect x="80" y="150" width="179" height="320" fill="none" stroke="#54717a" strokeWidth="3"/>
        <path d="M291 116 H350 V330 Q350 382 304 382" fill="none" stroke="#d8d0bd" strokeWidth="10"/>
        <circle cx="169" cy="104" r="25" fill="#071c27" stroke="#d8d0bd" strokeWidth="7"/>
        <text x="169" y="570" textAnchor="middle" fill="#e9dfc8" fontSize="78" fontWeight="700">3.40</text>
        <text x="169" y="612" textAnchor="middle" fill="#9eb4b0" fontFamily="Arial, sans-serif" fontSize="23" letterSpacing="4">Q4 2026</text>
      </g>
    </svg>
    <div style={{position:'absolute',left:'8%',right:'8%',top:'10%',height:34,display:'flex',justifyContent:'flex-end',alignItems:'center',fontFamily:'Arial, sans-serif',fontSize:14,letterSpacing:3,color:'#8aa5a7'}}>{sourceLabel ? <span>{sourceLabel}</span> : null}</div>
  </AbsoluteFill>;
};

const Shot_m20: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.max(0, Math.min(1, progress));
  const needle = interpolate(p, [0, 0.68, 1], [-28, -57, -57], {extrapolateLeft:'clamp', extrapolateRight:'clamp'});
  const glow = interpolate(p, [0.62, 0.84, 1], [0, 1, 0.35], {extrapolateLeft:'clamp', extrapolateRight:'clamp'});
  const angle = needle * Math.PI / 180;
  const x2 = 800 + Math.cos(angle) * 250;
  const y2 = 600 + Math.sin(angle) * 250;
  return <AbsoluteFill style={{backgroundColor:'#f2eee4', color:'#112e38', fontFamily:'Georgia, serif', overflow:'hidden'}}>
    <svg width={width} height={height} viewBox="0 0 1600 900" style={{position:'absolute',inset:0}}>
      <defs><radialGradient id="m20wash"><stop offset="0" stopColor="#f2ac45" stopOpacity="0.2"/><stop offset="1" stopColor="#f2eee4" stopOpacity="0"/></radialGradient></defs>
      <rect width="1600" height="900" fill="#f2eee4"/>
      <ellipse cx="800" cy="484" rx="510" ry="405" fill="url(#m20wash)" opacity={glow}/>
      <path d="M340 600 A460 460 0 0 1 1260 600" fill="none" stroke="#204450" strokeWidth="26"/>
      <path d="M370 600 A430 430 0 0 1 1230 600" fill="none" stroke="#c8bfae" strokeWidth="3" strokeDasharray="3 20"/>
      <line x1="800" y1="600" x2={x2} y2={y2} stroke="#d78b32" strokeWidth="15" strokeLinecap="round"/>
      <circle cx="800" cy="600" r="34" fill="#112e38"/>
      <circle cx="800" cy="600" r="13" fill="#f2ac45"/>
      <text x="800" y="224" textAnchor="middle" fill="#112e38" fontSize="52" fontWeight="700" letterSpacing="3">INFLATION COMPENSATION</text>
      <text x="800" y="754" textAnchor="middle" fill="#54717a" fontFamily="Arial, sans-serif" fontSize="23" letterSpacing="4">SUSTAINED RETREAT IN OIL</text>
    </svg>
    <div style={{position:'absolute',left:'8%',right:'8%',top:'10%',height:34,display:'flex',justifyContent:'flex-end',alignItems:'center',fontFamily:'Arial, sans-serif',fontSize:14,letterSpacing:3,color:'#607e82'}}>{sourceLabel ? <span>{sourceLabel}</span> : null}</div>
  </AbsoluteFill>;
};

const Shot_m21: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.min(1, Math.max(0, progress));
  const leftEdge = interpolate(p,[0,0.45,1],[1,0.55,0.25]);
  const rightGlow = interpolate(p,[0,0.4,1],[0.15,0.8,1]);
  const arrowA = interpolate(p,[0,0.35,1],[0,1,1]);
  const arrowB = interpolate(p,[0,0.55,1],[0,0.5,1]);
  return <AbsoluteFill style={{background:'#f4efe6',color:'#18232a',fontFamily:'Georgia, serif'}}>
    <AbsoluteFill style={{padding:'10% 8%',boxSizing:'border-box'}}>
      <div style={{position:'absolute',inset:'10% 8%',border:'1px solid rgba(24,35,42,.15)'}} />
      <div style={{position:'absolute',top:'12%',left:'8%',fontFamily:'Arial, sans-serif',fontSize:18,letterSpacing:4,color:'#7b8078'}}>CROSS-ASSET CHANNEL</div>
      <svg viewBox="0 0 1600 900" style={{position:'absolute',inset:0,width:'100%',height:'100%'}}>
        <defs><linearGradient id="amber21" x1="0" x2="1"><stop stopColor="#c57b2c" stopOpacity=".25"/><stop offset="1" stopColor="#d99a42"/></linearGradient><filter id="glow21"><feGaussianBlur stdDeviation="10"/></filter></defs>
        <path d="M170 700 C230 520 220 280 390 190 C510 130 610 190 650 340 L650 700 Z" fill="#24343a" opacity=".96"/>
        <path d="M1190 700 C1150 560 1160 350 1260 260 C1370 160 1470 300 1490 700 Z" fill="#304047" opacity=".95"/>
        <path d="M360 710 L360 590 M360 590 C360 520 420 490 470 520 L470 710" fill="none" stroke="#f4efe6" strokeWidth="12" opacity=".3"/>
        <path d="M1290 700 L1290 500 M1290 500 C1290 430 1350 400 1400 440 L1400 700" fill="none" stroke="#f4efe6" strokeWidth="12" opacity=".3"/>
        <path d="M520 320 C780 250 950 270 1190 350" fill="none" stroke="#d8953e" strokeWidth="34" opacity={rightGlow*.28} filter="url(#glow21)"/>
        <path d="M520 320 C780 250 950 270 1190 350" fill="none" stroke="url(#amber21)" strokeWidth="12" strokeDasharray="32 22" strokeDashoffset={-frame*.8}/>
        <path d="M520 320 l48 -24 l-14 45" fill="#d8953e" opacity={arrowA}/>
        <path d="M780 280 l48 -24 l-14 45" fill="#d8953e" opacity={arrowB}/>
        <path d="M1040 310 l48 -24 l-14 45" fill="#d8953e" opacity={rightGlow}/>
        <path d="M490 610 C700 650 900 650 1120 590" fill="none" stroke="#c57b2c" strokeWidth="9" opacity={leftEdge} strokeDasharray="18 25"/>
        <circle cx="520" cy="320" r="16" fill="#d8953e"/><circle cx="1190" cy="350" r="20" fill="#d8953e" opacity={rightGlow}/>
      </svg>
      <div style={{position:'absolute',bottom:'13%',left:'8%',fontFamily:'Arial, sans-serif',fontSize:22,letterSpacing:3,color:'#24343a'}}>IMPORTER</div>
      <div style={{position:'absolute',bottom:'13%',right:'8%',fontFamily:'Arial, sans-serif',fontSize:22,letterSpacing:3,color:'#24343a'}}>PRODUCER</div>
      <div style={{position:'absolute',bottom:'5%',right:'8%',fontFamily:'Arial, sans-serif',fontSize:14,letterSpacing:2,color:'#7b8078'}}>{sourceLabel}</div>
    </AbsoluteFill>
  </AbsoluteFill>;
};

const Shot_m22: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.min(1, Math.max(0, progress));
  const inflation = interpolate(p,[0,.65,1],[.58,.3,.34]);
  const policy = interpolate(p,[0,.35,1],[.16,.72,.48]);
  const arc = (cx:number,cy:number,r:number) => `M ${cx-r} ${cy} A ${r} ${r} 0 0 1 ${cx+r} ${cy}`;
  return <AbsoluteFill style={{background:'#eef0eb',fontFamily:'Georgia, serif',color:'#1d2c31'}}>
    <div style={{position:'absolute',inset:'10% 8%',border:'1px solid rgba(29,44,49,.14)'}} />
    <div style={{position:'absolute',top:'12%',left:'8%',fontFamily:'Arial, sans-serif',fontSize:18,letterSpacing:4,color:'#77817d'}}>SIGNAL / RESPONSE</div>
    <div style={{position:'absolute',left:'8%',right:'8%',top:'25%',height:'55%',display:'flex',gap:'8%',alignItems:'center'}}>
      {[{label:'INFLATION',value:inflation,accent:'#c27a2b'},{label:'POLICY',value:policy,accent:'#2c6970'}].map((g,i)=><div key={g.label} style={{flex:1,height:'100%',position:'relative'}}>
        <svg viewBox="0 0 500 320" style={{width:'100%',height:'100%'}}>
          <path d={arc(250,220,150)} fill="none" stroke="#cad0c9" strokeWidth="28" strokeLinecap="round"/>
          <path d={arc(250,220,150)} fill="none" stroke={g.accent} strokeWidth="8" strokeDasharray="235 500" strokeDashoffset={i===0?interpolate(g.value,[0,1],[10,-170]):0} opacity=".85"/>
          {[0,1,2,3,4].map(n=>{const a=Math.PI-(Math.PI*n/4);return <line key={n} x1={250+125*Math.cos(a)} y1={220-125*Math.sin(a)} x2={250+150*Math.cos(a)} y2={220-150*Math.sin(a)} stroke="#74807a" strokeWidth="4"/>;})}
          <line x1="250" y1="220" x2={250+112*Math.cos(Math.PI-(Math.PI*g.value))} y2={220-112*Math.sin(Math.PI-(Math.PI*g.value))} stroke={g.accent} strokeWidth="12" strokeLinecap="round"/>
          <circle cx="250" cy="220" r="18" fill={g.accent}/>
        </svg>
        <div style={{position:'absolute',bottom:'4%',left:0,right:0,textAlign:'center',fontFamily:'Arial, sans-serif',fontSize:25,letterSpacing:5}}>{g.label}</div>
      </div>)}
    </div>
    <div style={{position:'absolute',bottom:'13%',left:'8%',fontSize:24,color:'#7a4d29'}}>CHEAPER GASOLINE ≠ COMPLETE SIGNAL</div>
    <div style={{position:'absolute',bottom:'5%',right:'8%',fontFamily:'Arial, sans-serif',fontSize:14,letterSpacing:2,color:'#77817d'}}>{sourceLabel}</div>
  </AbsoluteFill>;
};

const Shot_m23: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.min(1, Math.max(0, progress));
  const spin = frame*.8;
  const needle = interpolate(p,[0,.45,1],[.22,.65,.4]);
  const items = [{t:'PRICE PERSISTENCE',r:230,a:spin*.7},{t:'LABOR',r:300,a:-spin*1.15},{t:'EXPECTATIONS',r:235,a:spin*1.55}];
  return <AbsoluteFill style={{background:'#f4efe6',color:'#192b31',fontFamily:'Georgia, serif'}}>
    <div style={{position:'absolute',inset:'10% 8%',border:'1px solid rgba(25,43,49,.14)'}} />
    <div style={{position:'absolute',top:'12%',left:'8%',fontFamily:'Arial, sans-serif',fontSize:18,letterSpacing:4,color:'#7b8078'}}>BROADER POLICY INPUTS</div>
    <svg viewBox="0 0 1600 900" style={{position:'absolute',inset:0,width:'100%',height:'100%'}}>
      <circle cx="800" cy="480" r="210" fill="none" stroke="#d0d2c9" strokeWidth="2" strokeDasharray="5 16"/>
      <circle cx="800" cy="480" r="108" fill="#eef0e8" stroke="#2c6970" strokeWidth="7"/>
      <path d="M800 480 L800 390" stroke="#c27a2b" strokeWidth="12" strokeLinecap="round" transform={`rotate(${needle*115-55} 800 480)`}/><circle cx="800" cy="480" r="14" fill="#c27a2b"/>
      {items.map((it,i)=>{const rad=(it.a-90)*Math.PI/180;const x=800+it.r*Math.cos(rad);const y=480+it.r*Math.sin(rad);return <g key={it.t} transform={`translate(${x} ${y})`}><circle r="22" fill="#c27a2b" opacity=".9"/><circle r="38" fill="none" stroke="#c27a2b" strokeOpacity=".25" strokeWidth="3"/><text x="0" y="72" textAnchor="middle" fill="#192b31" fontSize="22" letterSpacing="3" fontFamily="Arial, sans-serif">{it.t}</text></g>;})}
      <text x="800" y="555" textAnchor="middle" fill="#2c6970" fontSize="21" letterSpacing="4" fontFamily="Arial, sans-serif">POLICY</text>
    </svg>
    <div style={{position:'absolute',bottom:'5%',right:'8%',fontFamily:'Arial, sans-serif',fontSize:14,letterSpacing:2,color:'#7b8078'}}>{sourceLabel}</div>
  </AbsoluteFill>;
};

const Shot_m24: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.min(1, Math.max(0, progress));
  const rotation = interpolate(p,[0,1],[0,135]);
  const first = interpolate(p,[0,.58,1],[0,1,1]);
  const second = interpolate(p,[0,.75,1],[0,0,1]);
  return <AbsoluteFill style={{background:'#edf0eb',color:'#1d2d32',fontFamily:'Georgia, serif'}}>
    <div style={{position:'absolute',inset:'10% 8%',border:'1px solid rgba(29,45,50,.14)'}} />
    <div style={{position:'absolute',top:'12%',left:'8%',fontFamily:'Arial, sans-serif',fontSize:18,letterSpacing:4,color:'#77817d'}}>NEXT EVIDENCE</div>
    <svg viewBox="0 0 1600 900" style={{position:'absolute',inset:0,width:'100%',height:'100%'}}>
      <g transform={`rotate(${rotation} 800 470)`}>
        <circle cx="800" cy="470" r="230" fill="none" stroke="#cbd1c9" strokeWidth="3" strokeDasharray="12 20"/>
        <circle cx="800" cy="470" r="170" fill="none" stroke="#d89a42" strokeWidth="5" strokeDasharray="2 24"/>
      </g>
      <g opacity={first}><line x1="800" y1="240" x2="800" y2="300" stroke="#c27a2b" strokeWidth="5"/><circle cx="800" cy="220" r="25" fill="#c27a2b"/><text x="800" y="150" textAnchor="middle" fontSize="30" letterSpacing="4" fill="#192b31" fontFamily="Arial, sans-serif">JUL 15</text></g>
      <g opacity={second}><line x1="1230" y1="470" x2="1170" y2="470" stroke="#c27a2b" strokeWidth="5"/><circle cx="1250" cy="470" r="25" fill="#c27a2b"/><text x="1250" y="540" textAnchor="middle" fontSize="30" letterSpacing="4" fill="#192b31" fontFamily="Arial, sans-serif">AUG 11</text></g>
      <circle cx="800" cy="470" r="65" fill="#f4efe6" stroke="#2c6970" strokeWidth="6"/><text x="800" y="478" textAnchor="middle" fontSize="21" letterSpacing="4" fill="#2c6970" fontFamily="Arial, sans-serif">EVENTS</text>
    </svg>
    <div style={{position:'absolute',bottom:'5%',right:'8%',fontFamily:'Arial, sans-serif',fontSize:14,letterSpacing:2,color:'#77817d'}}>{sourceLabel}</div>
  </AbsoluteFill>;
};

const Shot_m25: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => {
  const p = Math.min(1, Math.max(0, progress));
  const x = interpolate(p,[0,1],[1060,570]);
  const lift = spring({frame,fps,config:{damping:18,stiffness:80,mass:1},from:0,to:1});
  const line = interpolate(p,[0,.45,1],[0,1,1]);
  return <AbsoluteFill style={{background:'#f4efe6',color:'#1a2b31',fontFamily:'Georgia, serif'}}>
    <div style={{position:'absolute',inset:'10% 8%',border:'1px solid rgba(26,43,49,.14)'}} />
    <div style={{position:'absolute',top:'12%',left:'8%',fontFamily:'Arial, sans-serif',fontSize:18,letterSpacing:4,color:'#7b8078'}}>FIRST CHECKPOINT</div>
    <svg viewBox="0 0 1600 900" style={{position:'absolute',inset:0,width:'100%',height:'100%'}}>
      <path d="M420 590 C650 500 820 430 1080 330" fill="none" stroke="#d4943c" strokeWidth="8" strokeDasharray="16 18" strokeDashoffset={-frame*.7} opacity={line}/>
      <circle cx="420" cy="590" r="22" fill="#c27a2b"/><text x="420" y="680" textAnchor="middle" fontSize="28" letterSpacing="3" fill="#1a2b31" fontFamily="Arial, sans-serif">JUL 15</text>
      <g transform={`translate(${x} ${300-(lift*18)})`}>
        <rect x="-370" y="-65" width="740" height="130" rx="5" fill="#20353b"/>
        <rect x="-345" y="-40" width="690" height="80" fill="#eef0e9"/>
        <line x1="-320" y1="-12" x2="-260" y2="-12" stroke="#d4943c" strokeWidth="8"/><line x1="-240" y1="-12" x2="300" y2="-12" stroke="#b9c0b8" strokeWidth="5"/>
        <text x="-320" y="22" fontSize="24" letterSpacing="3" fill="#20353b" fontFamily="Arial, sans-serif">WEEKLY PETROLEUM STATUS REPORT</text>
      </g>
      <path d="M1080 365 L1080 590" stroke="#2c6970" strokeWidth="4" opacity=".5"/>
      <circle cx="1080" cy="590" r="14" fill="#2c6970"/>
    </svg>
    <div style={{position:'absolute',bottom:'5%',right:'8%',fontFamily:'Arial, sans-serif',fontSize:14,letterSpacing:2,color:'#7b8078'}}>{sourceLabel}</div>
  </AbsoluteFill>;
};

const Shot_m26: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => { const amber = '#F2A93B'; const ink = '#091317'; const paper = '#E8E0CF'; const draw = interpolate(progress,[0.08,0.48],[1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.bezier(0.22,0.8,0.24,1)}); const onward = interpolate(progress,[0.5,0.92],[1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.cubic)}); const pinScale = spring({frame:frame-fps*0.55,fps,config:{damping:13,stiffness:155,mass:0.75}}); const pulse = 0.68+0.32*Math.sin(frame/fps*Math.PI*3); return <AbsoluteFill aria-label={narration} style={{backgroundColor:ink,color:paper,overflow:'hidden',fontFamily:'Avenir Next Condensed, Franklin Gothic Medium, sans-serif'}}><svg viewBox='0 0 1600 900' width='100%' height='100%' style={{position:'absolute',inset:0}}><defs><linearGradient id='m26Bg' x1='0' y1='0' x2='1' y2='1'><stop stopColor='#12242A'/><stop offset='1' stopColor='#071014'/></linearGradient><filter id='m26Glow'><feGaussianBlur stdDeviation='7' result='b'/><feMerge><feMergeNode in='b'/><feMergeNode in='SourceGraphic'/></feMerge></filter></defs><rect width='1600' height='900' fill='url(#m26Bg)'/><path d='M0 710 C260 650 420 698 600 600' fill='none' stroke='#183239' strokeWidth='2'/><path d='M278 504 C520 504 672 504 914 504' fill='none' stroke='#5B4B2C' strokeWidth='7'/><path d='M278 504 C520 504 672 504 914 504' pathLength={1} fill='none' stroke={amber} strokeWidth='7' strokeLinecap='round' strokeDasharray={1} strokeDashoffset={draw}/><path d='M914 504 C1100 504 1290 430 1640 430' pathLength={1} fill='none' stroke={amber} strokeWidth='7' strokeLinecap='round' strokeDasharray={1} strokeDashoffset={onward} opacity={0.92}/><circle cx='278' cy='504' r='13' fill={ink} stroke={amber} strokeWidth='5'/><line x1='278' y1='491' x2='278' y2='355' stroke={amber} strokeWidth='4'/><text x='278' y='318' textAnchor='middle' fill='#9AA9A8' fontSize='23' letterSpacing='5'>JUL 15</text><g transform={`translate(914 504) scale(${Math.max(0,pinScale)})`} filter='url(#m26Glow)'><circle r='23' fill={amber} opacity={pulse}/><circle r='10' fill='#FFF3D0'/><path d='M0 -22 L0 -156' stroke={amber} strokeWidth='6' strokeLinecap='round'/><path d='M-22 -156 L22 -156 L0 -188 Z' fill={amber}/></g><text x='914' y='274' textAnchor='middle' fill={paper} fontSize='76' fontWeight='700' letterSpacing='3'>AUG 11</text><text x='914' y='324' textAnchor='middle' fill={amber} fontSize='22' letterSpacing='7'>SHORT-TERM ENERGY OUTLOOK</text><circle cx={914+interpolate(progress,[0.5,1],[0,650],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})} cy={interpolate(progress,[0.5,1],[504,430],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})} r='7' fill='#FFF3D0' opacity={progress>0.5?1:0}/></svg><div style={{position:'absolute',left:width*0.08,top:height*0.1,fontSize:13,letterSpacing:4,color:'#718589'}}>RELEASE ROUTE / 02</div>{sourceLabel?<div style={{position:'absolute',right:width*0.08,bottom:height*0.1,fontSize:12,letterSpacing:2,color:'#718589',textTransform:'uppercase'}}>{sourceLabel}</div>:null}</AbsoluteFill>; };

const Shot_m27: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => { const amber = '#F2A93B'; const ink = '#081418'; const waterTop = interpolate(progress,[0.08,0.88],[626,580],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.cubic)}); const demandPulse = interpolate(Math.sin(frame/fps*Math.PI*1.4),[-1,1],[0.35,1]); const drops = [0,0.22,0.44,0.66,0.88]; return <AbsoluteFill aria-label={narration} style={{backgroundColor:ink,color:'#EEE6D5',overflow:'hidden',fontFamily:'Avenir Next Condensed, Franklin Gothic Medium, sans-serif'}}><svg viewBox='0 0 1600 900' width='100%' height='100%' style={{position:'absolute',inset:0}}><defs><linearGradient id='m27Bg' x1='0' y1='0' x2='0' y2='1'><stop stopColor='#11262B'/><stop offset='1' stopColor='#061014'/></linearGradient><linearGradient id='m27Water' x1='0' y1='0' x2='1' y2='0'><stop stopColor='#6E431D'/><stop offset='0.55' stopColor='#B46B22'/><stop offset='1' stopColor='#68421F'/></linearGradient><clipPath id='m27Basin'><path d='M260 500 L360 748 Q800 812 1240 748 L1340 500 Z'/></clipPath><filter id='m27Soft'><feGaussianBlur stdDeviation='9'/></filter></defs><rect width='1600' height='900' fill='url(#m27Bg)'/><path d='M260 500 L360 748 Q800 812 1240 748 L1340 500' fill='none' stroke='#708081' strokeWidth='5'/><g clipPath='url(#m27Basin)'><rect x='245' y={waterTop} width='1110' height={820-waterTop} fill='url(#m27Water)' opacity='0.8'/><ellipse cx='800' cy={waterTop} rx='535' ry='35' fill='#E59A35' opacity='0.22'/><path d={`M270 ${waterTop} C470 ${waterTop-14} 620 ${waterTop+12} 800 ${waterTop} C990 ${waterTop-14} 1135 ${waterTop+13} 1330 ${waterTop}`} fill='none' stroke='#F5C875' strokeWidth='4' opacity='0.65'/></g>{drops.map((offset,index)=>{ const phase=(progress+offset)%1; const y=interpolate(phase,[0,0.78,0.79,1],[190,waterTop-12,waterTop,waterTop],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}); const opacity=phase<0.79?interpolate(phase,[0,0.12,0.78],[0,1,0.9],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}):0; return <g key={index}><path d={`M${485+index*155} 162 L${485+index*155} 210`} stroke='#5C482C' strokeWidth='3'/><circle cx={485+index*155} cy={y} r={8+index%2*2} fill={amber} opacity={opacity}/></g>;})}<path d='M190 545 C365 520 470 566 620 530 C770 494 900 510 1040 482 C1170 456 1295 470 1430 424' fill='none' stroke='#263A3D' strokeWidth='14' strokeLinecap='round'/><path d='M190 545 C365 520 470 566 620 530 C770 494 900 510 1040 482 C1170 456 1295 470 1430 424' pathLength={1} fill='none' stroke='#F7C66B' strokeWidth='5' strokeLinecap='round' strokeDasharray='0.09 0.91' strokeDashoffset={-((progress*0.72)%1)} opacity={demandPulse}/><g transform='translate(1300 390)'><rect x='-92' y='-31' width='184' height='55' rx='4' fill='#132327' stroke='#C9903A'/><text textAnchor='middle' y='7' fill='#F5D9A2' fontSize='23' letterSpacing='4'>DEMAND</text></g><text x='800' y='693' textAnchor='middle' fill='#FFF0CE' fontSize='48' fontWeight='700' letterSpacing='8'>INVENTORIES</text><text x='800' y='125' textAnchor='middle' fill={amber} fontSize='24' letterSpacing='9'>BARRELS</text></svg><div style={{position:'absolute',left:width*0.08,top:height*0.1,fontSize:13,letterSpacing:4,color:'#718589'}}>MARKET TESTS / COMBINED</div>{sourceLabel?<div style={{position:'absolute',right:width*0.08,bottom:height*0.1,fontSize:12,letterSpacing:2,color:'#718589',textTransform:'uppercase'}}>{sourceLabel}</div>:null}</AbsoluteFill>; };

const Shot_m28: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => { const amber = '#F2A93B'; const ink = '#071216'; const reveal = interpolate(progress,[0.02,0.54],[1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.bezier(0.18,0.84,0.3,1)}); const returnPulse = interpolate(progress,[0.58,0.94],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.cubic)}); const valveTurn = interpolate(progress,[0.2,0.62],[0,38],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}); const route = 'M-40 470 C140 470 180 355 340 355 L520 355 C610 355 620 505 720 505 L945 505 C1010 505 1015 610 1105 610 L1640 610'; return <AbsoluteFill aria-label={narration} style={{backgroundColor:ink,color:'#F0E8D8',overflow:'hidden',fontFamily:'Avenir Next Condensed, Franklin Gothic Medium, sans-serif'}}><svg viewBox='0 0 1600 900' width='100%' height='100%' style={{position:'absolute',inset:0}}><defs><radialGradient id='m28Bg'><stop stopColor='#183038'/><stop offset='1' stopColor='#061014'/></radialGradient><filter id='m28Glow'><feGaussianBlur stdDeviation='10' result='g'/><feMerge><feMergeNode in='g'/><feMergeNode in='SourceGraphic'/></feMerge></filter></defs><rect width='1600' height='900' fill='url(#m28Bg)'/><path d={route} fill='none' stroke='#294148' strokeWidth='18' strokeLinecap='round'/><path d={route} pathLength={1} fill='none' stroke={amber} strokeWidth='8' strokeLinecap='round' strokeDasharray={1} strokeDashoffset={reveal}/><path d={route} pathLength={1} fill='none' stroke='#FFF0C3' strokeWidth='5' strokeLinecap='round' strokeDasharray='0.055 0.945' strokeDashoffset={returnPulse} opacity={returnPulse} filter='url(#m28Glow)'/><g transform={`translate(520 355) rotate(${valveTurn})`}><circle r='55' fill={ink} stroke={amber} strokeWidth='7'/><line x1='-36' y1='0' x2='36' y2='0' stroke={amber} strokeWidth='8'/><line x1='0' y1='-36' x2='0' y2='36' stroke={amber} strokeWidth='8'/></g><g transform={`translate(945 505) rotate(${-valveTurn*0.7})`}><circle r='47' fill={ink} stroke={amber} strokeWidth='7'/><path d='M-30 0 L30 0 M0 -30 L0 30' stroke={amber} strokeWidth='7'/></g><path d='M1080 610 L1130 754 Q1335 792 1530 754 L1575 610' fill='#51351F' fillOpacity='0.5' stroke='#788787' strokeWidth='4'/><ellipse cx='1327' cy='666' rx='230' ry='35' fill={amber} opacity='0.38'/><circle cx={interpolate(progress,[0.06,0.58],[-20,1328],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})} cy={interpolate(progress,[0.06,0.24,0.38,0.58],[470,355,505,610],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})} r='10' fill='#FFF3D0' filter='url(#m28Glow)'/><text x='180' y='292' fill='#93A2A2' fontSize='22' letterSpacing='6'>ROUTE</text><text x='520' y='260' textAnchor='middle' fill='#F5C26B' fontSize='22' letterSpacing='6'>BARRELS</text><text x='945' y='420' textAnchor='middle' fill='#F5C26B' fontSize='22' letterSpacing='6'>DEMAND</text><text x='1325' y='730' textAnchor='middle' fill='#FFF0CD' fontSize='28' letterSpacing='6'>INVENTORIES</text><text x='800' y='150' textAnchor='middle' fill='#F3E9D5' fontSize='62' fontWeight='700' letterSpacing='4'>THE RECOVERY ROUTE</text></svg><div style={{position:'absolute',left:width*0.08,top:height*0.1,fontSize:13,letterSpacing:4,color:'#718589'}}>MECHANISM / CONNECTED</div>{sourceLabel?<div style={{position:'absolute',right:width*0.08,bottom:height*0.1,fontSize:12,letterSpacing:2,color:'#718589',textTransform:'uppercase'}}>{sourceLabel}</div>:null}</AbsoluteFill>; };

const Shot_m29: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => { const amber = '#F2A93B'; const ink = '#071216'; const trunkDraw = interpolate(progress,[0.02,0.3],[1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.out(Easing.cubic)}); const forkDraw = interpolate(progress,[0.24,0.62],[1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.bezier(0.2,0.75,0.2,1)}); const priceGlow = interpolate(progress,[0.3,0.48,0.7,0.9],[0.25,1,0.82,0.42],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}); const labelIn = spring({frame:frame-fps*0.72,fps,config:{damping:18,stiffness:120,mass:0.9}}); return <AbsoluteFill aria-label={narration} style={{backgroundColor:ink,color:'#EEE6D7',overflow:'hidden',fontFamily:'Avenir Next Condensed, Franklin Gothic Medium, sans-serif'}}><svg viewBox='0 0 1600 900' width='100%' height='100%' style={{position:'absolute',inset:0}}><defs><linearGradient id='m29Bg' x1='0' y1='0' x2='1' y2='1'><stop stopColor='#10262C'/><stop offset='1' stopColor='#050D11'/></linearGradient><filter id='m29Glow'><feGaussianBlur stdDeviation='15' result='b'/><feMerge><feMergeNode in='b'/><feMergeNode in='SourceGraphic'/></feMerge></filter></defs><rect width='1600' height='900' fill='url(#m29Bg)'/><path d='M-20 450 L750 450' fill='none' stroke='#31454A' strokeWidth='20'/><path d='M750 450 L1240 260' fill='none' stroke='#3B3F3B' strokeWidth='20'/><path d='M750 450 L1240 655' fill='none' stroke='#242E31' strokeWidth='20'/><path d='M-20 450 L750 450' pathLength={1} fill='none' stroke={amber} strokeWidth='9' strokeDasharray={1} strokeDashoffset={trunkDraw}/><path d='M750 450 L1240 260' pathLength={1} fill='none' stroke={amber} strokeWidth='10' strokeLinecap='round' strokeDasharray={1} strokeDashoffset={forkDraw} opacity={priceGlow} filter='url(#m29Glow)'/><path d='M750 450 L1240 655' pathLength={1} fill='none' stroke='#596467' strokeWidth='7' strokeLinecap='round' strokeDasharray={1} strokeDashoffset={forkDraw} opacity='0.48'/><circle cx='750' cy='450' r='30' fill={ink} stroke={amber} strokeWidth='8'/><circle cx='750' cy='450' r='9' fill='#FFF0C5'/><g transform={`translate(1265 260) scale(${Math.max(0,labelIn)})`}><rect x='-194' y='-67' width='388' height='134' rx='5' fill='#1B211E' stroke={amber} strokeWidth='4' opacity={0.72+priceGlow*0.28}/><text textAnchor='middle' y='18' fill='#FFF0C8' fontSize='57' fontWeight='700' letterSpacing='9'>PRICE</text></g><g transform={`translate(1265 655) scale(${Math.max(0,labelIn)})`} opacity='0.42'><rect x='-194' y='-67' width='388' height='134' rx='5' fill='#10191C' stroke='#667274' strokeWidth='3'/><text textAnchor='middle' y='17' fill='#9EA8A8' fontSize='43' fontWeight='700' letterSpacing='7'>DURABILITY</text></g><text x='750' y='350' textAnchor='middle' fill='#9EABAA' fontSize='19' letterSpacing='6'>THE FORK</text></svg><div style={{position:'absolute',left:width*0.08,top:height*0.1,fontSize:13,letterSpacing:4,color:'#718589'}}>RECOVERY / TEST OF STAYING POWER</div>{sourceLabel?<div style={{position:'absolute',right:width*0.08,bottom:height*0.1,fontSize:12,letterSpacing:2,color:'#718589',textTransform:'uppercase'}}>{sourceLabel}</div>:null}</AbsoluteFill>; };

const Shot_m30: React.FC<AuthoredShotProps> = ({frame,fps,width,height,progress,assetPath,assetClass,narration,sourceLabel}) => { const amber = '#F2A93B'; const ink = '#050E12'; const arrival = interpolate(progress,[0.04,0.46],[260,1188],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.bezier(0.18,0.82,0.25,1)}); const ripple = interpolate(progress,[0.43,0.78],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.out(Easing.cubic)}); const textIn = spring({frame:frame-fps*0.45,fps,config:{damping:20,stiffness:105,mass:1.05}}); const fade = interpolate(progress,[0.86,1],[1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.cubic)}); return <AbsoluteFill aria-label={narration} style={{backgroundColor:'#000',overflow:'hidden',fontFamily:'Avenir Next Condensed, Franklin Gothic Medium, sans-serif'}}><AbsoluteFill style={{opacity:fade,backgroundColor:ink,color:'#F1E9D8'}}><svg viewBox='0 0 1600 900' width='100%' height='100%' style={{position:'absolute',inset:0}}><defs><linearGradient id='m30Sky' x1='0' y1='0' x2='0' y2='1'><stop stopColor='#132A30'/><stop offset='0.72' stopColor='#09171B'/><stop offset='1' stopColor='#061014'/></linearGradient><linearGradient id='m30Water' x1='0' y1='0' x2='0' y2='1'><stop stopColor='#243A3C'/><stop offset='1' stopColor='#071115'/></linearGradient><filter id='m30Glow'><feGaussianBlur stdDeviation='9' result='b'/><feMerge><feMergeNode in='b'/><feMergeNode in='SourceGraphic'/></feMerge></filter></defs><rect width='1600' height='900' fill='url(#m30Sky)'/><path d='M0 470 C310 458 535 485 800 470 C1090 454 1320 480 1600 468 L1600 900 L0 900 Z' fill='url(#m30Water)'/><path d='M0 470 C310 458 535 485 800 470 C1090 454 1320 480 1600 468' fill='none' stroke='#627676' strokeWidth='3' opacity='0.7'/><g transform={`translate(${arrival} 445)`}><circle r='8' fill={amber} filter='url(#m30Glow)'/><path d='M-34 5 L-12 5 L-4 -12 L14 -12 L20 5 L38 5 L27 17 L-25 17 Z' fill='#DFA64B'/><path d='M-88 21 L-42 21' stroke='#7F693F' strokeWidth='3' opacity='0.7'/></g><ellipse cx='1188' cy='492' rx={35+255*ripple} ry={8+48*ripple} fill='none' stroke={amber} strokeWidth={interpolate(ripple,[0,1],[7,2])} opacity={interpolate(ripple,[0,0.72,1],[0,0.78,0.46])}/><ellipse cx='1188' cy='492' rx={18+145*ripple} ry={5+28*ripple} fill='none' stroke='#F8D28B' strokeWidth='3' opacity={interpolate(ripple,[0,0.5,1],[0,0.7,0.35])}/><g transform={`translate(800 0) scale(${Math.max(0,textIn)}) translate(-800 0)`}><text x='800' y='190' textAnchor='middle' fill='#F5EBD8' fontSize='28' letterSpacing='11'>WATCH</text><text x='800' y='285' textAnchor='middle' fill={amber} fontSize='77' fontWeight='700' letterSpacing='7'>BARRELS.</text><text x='800' y='365' textAnchor='middle' fill='#F5EBD8' fontSize='64' fontWeight='700' letterSpacing='6'>INVENTORIES. DEMAND.</text></g><path d='M335 405 L1265 405' stroke='#475858' strokeWidth='1'/></svg><div style={{position:'absolute',left:width*0.08,top:height*0.1,fontSize:13,letterSpacing:4,color:'#718589'}}>FINAL WATCHLIST</div>{sourceLabel?<div style={{position:'absolute',right:width*0.08,bottom:height*0.1,fontSize:12,letterSpacing:2,color:'#718589',textTransform:'uppercase'}}>{sourceLabel}</div>:null}</AbsoluteFill></AbsoluteFill>; };

export const authoredShots: Record<string, React.FC<AuthoredShotProps>> = {
  "s01": Shot_s01,
  "s02": Shot_s02,
  "s03": Shot_s03,
  "s04": Shot_s04,
  "s05": Shot_s05,
  "s06": Shot_s06,
  "s07": Shot_s07,
  "s08": Shot_s08,
  "s09": Shot_s09,
  "s10": Shot_s10,
  "s11": Shot_s11,
  "s12": Shot_s12,
  "s13": Shot_s13,
  "s14": Shot_s14,
  "m01": Shot_m01,
  "m02": Shot_m02,
  "m03": Shot_m03,
  "m04": Shot_m04,
  "m05": Shot_m05,
  "m06": Shot_m06,
  "m07": Shot_m07,
  "m08": Shot_m08,
  "m09": Shot_m09,
  "m10": Shot_m10,
  "m11": Shot_m11,
  "m12": Shot_m12,
  "m13": Shot_m13,
  "m14": Shot_m14,
  "m15": Shot_m15,
  "m16": Shot_m16,
  "m17": Shot_m17,
  "m18": Shot_m18,
  "m19": Shot_m19,
  "m20": Shot_m20,
  "m21": Shot_m21,
  "m22": Shot_m22,
  "m23": Shot_m23,
  "m24": Shot_m24,
  "m25": Shot_m25,
  "m26": Shot_m26,
  "m27": Shot_m27,
  "m28": Shot_m28,
  "m29": Shot_m29,
  "m30": Shot_m30,
};

export const internalSourceLabelShotIds = new Set<string>(["s04"]);
