// CODEX_VIEWER_FACING_AUTHORSHIP — story-specific viewer composition.
import React from 'react';
import {
  AbsoluteFill,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export type Segment = {id: string; frames: number; text: string};
export type BreakingProps = {proofId: string; creativeSourceSha256: string; segments: Segment[]};

export const defaults: BreakingProps = {
  proofId: 'CENSUS_RETAIL_20260814_OWNER_REPAIR_V2',
  creativeSourceSha256: 'preview',
  segments: [
    {id: 'alert', frames: 190, text: 'Breaking: U.S. retail sales fell 0.6 percent in July, to 763.6 billion dollars.'},
    {id: 'what_hit', frames: 190, text: 'That decline clears Census’s 90 percent sampling margin. But the categories did not move together.'},
    {id: 'first_reaction', frames: 230, text: 'Autos fell 1.8 percent. Nonstore sales fell 2.2. Clothing rose 1.9, and food services rose 0.5.'},
    {id: 'primary_document', frames: 220, text: 'The primary release says the estimate is seasonally adjusted, but not adjusted for price changes.'},
    {id: 'headline_misses', frames: 200, text: 'So the headline is nominal. It does not tell us whether shoppers bought less, prices fell, or both.'},
    {id: 'why_matters', frames: 180, text: 'That distinction runs through revenue, inventory decisions, and the real-consumption read.'},
    {id: 'wit', frames: 150, text: 'One decimal gets the alert. Seven pages decide what it means.'},
    {id: 'checkpoint', frames: 280, text: 'Next: revisions, category breadth, and inflation-adjusted consumption. Census reports again September 16. One soft month is a signal, not a verdict.'},
    {id: 'resolve', frames: 60, text: ''},
  ],
};

const C = {
  navy: '#071722', ink: '#10212b', paper: '#f5f0e5', white: '#fffdf8',
  red: '#ef4b4f', teal: '#087f78', gold: '#d89a31', blue: '#2d6cdf', muted: '#58707e',
};
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

const Brand: React.FC<{dark?: boolean}> = ({dark = false}) => (
  <div style={{position: 'absolute', top: 52, right: 54, fontSize: 18, fontWeight: 900, letterSpacing: 2.4, zIndex: 90, color: dark ? C.white : C.ink}}>
    CAPITAL <span style={{color: C.red}}>CHRONICLE</span>
  </div>
);
const Source: React.FC<{children: React.ReactNode; dark?: boolean}> = ({children, dark = false}) => (
  <div style={{position: 'absolute', left: 54, right: 54, bottom: 46, fontSize: 20, fontWeight: 700, color: dark ? '#d5e3e8' : C.ink, zIndex: 90}}>{children}</div>
);
const Kicker: React.FC<{children: React.ReactNode; color?: string}> = ({children, color = C.red}) => (
  <div style={{color, fontSize: 24, fontWeight: 950, letterSpacing: 3, textTransform: 'uppercase', marginBottom: 20}}>{children}</div>
);
const Head: React.FC<{children: React.ReactNode; size?: number; color?: string}> = ({children, size = 86, color = C.ink}) => (
  <div style={{fontSize: size, lineHeight: 0.98, fontWeight: 950, letterSpacing: '-0.045em', color}}>{children}</div>
);
const Shell: React.FC<{children: React.ReactNode; bg?: string; color?: string}> = ({children, bg = C.paper, color = C.ink}) => (
  <AbsoluteFill style={{background: bg, color, fontFamily: 'Arial, Helvetica, sans-serif', overflow: 'hidden', padding: '118px 62px 110px'}}>
    <Brand dark={color === C.white}/>{children}
  </AbsoluteFill>
);
const Enter: React.FC<{children: React.ReactNode; delay?: number; x?: number; y?: number}> = ({children, delay = 0, x = 0, y = 30}) => {
  const frame = useCurrentFrame();
  const p = spring({frame: frame - delay, fps: 30, config: {damping: 20, stiffness: 155}});
  return <div style={{opacity: p, transform: `translate(${(1 - p) * x}px, ${(1 - p) * y}px)`}}>{children}</div>;
};
const Photo: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const z = interpolate(frame, [0, durationInFrames], [1.01, 1.065], clamp);
  const x = interpolate(frame, [0, durationInFrames], [0, -18], clamp);
  return <Img src={staticFile('assets/mall.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'center 42%', transform: `translateX(${x}px) scale(${z})`}}/>;
};

const Alert: React.FC = () => {
  const frame = useCurrentFrame();
  const line = interpolate(frame, [0, 24], [0, 1], clamp);
  const value = spring({frame: frame - 42, fps: 30, config: {damping: 18}});
  const margin = spring({frame: frame - 102, fps: 30, config: {damping: 20}});
  return (
    <Shell bg={C.navy} color={C.white}>
      <div style={{height: 10, width: `${180 * line}px`, background: C.red, marginTop: 170}}/>
      <Enter delay={8}><div style={{fontSize: 27, fontWeight: 900, color: C.red, letterSpacing: 4, marginTop: 48}}>BREAKING • 8:30 ET</div></Enter>
      <Enter delay={18}><Head size={108} color={C.white}>Retail sales<br/><span style={{color: C.red}}>fall 0.6%</span></Head></Enter>
      <div style={{marginTop: 44, fontSize: 45, fontWeight: 850, color: '#bed0d7', opacity: value, transform: `translateY(${(1 - value) * 24}px)`}}>$763.6B in July</div>
      <div style={{marginTop: 34, display: 'inline-flex', padding: '16px 20px', border: '2px solid #5f7884', color: '#d5e3e8', fontSize: 25, fontWeight: 800, opacity: margin}}>90% sampling margin: ±0.4 percentage point</div>
      <Source dark>U.S. Census Bureau • Advance retail release • Aug. 14, 2026</Source>
    </Shell>
  );
};

const WhatHit: React.FC = () => {
  const frame = useCurrentFrame();
  const card = spring({frame: frame - 20, fps: 30, config: {damping: 21}});
  const split = spring({frame: frame - 105, fps: 30, config: {damping: 18}});
  return (
    <AbsoluteFill style={{fontFamily: 'Arial, Helvetica, sans-serif'}}>
      <Photo/>
      <AbsoluteFill style={{background: 'linear-gradient(180deg,rgba(7,23,34,.02),rgba(7,23,34,.56))'}}/>
      <div style={{position: 'absolute', left: 62, right: 62, top: 460, padding: '42px 40px', background: 'rgba(255,253,248,.96)', borderLeft: `12px solid ${C.red}`, opacity: card, transform: `translateY(${(1 - card) * 45}px)`}}>
        <Kicker>What hit</Kicker><Head size={77}>A significant drop.</Head>
        <div style={{fontSize: 35, fontWeight: 850, marginTop: 30, color: C.muted}}>But not a one-direction category tape.</div>
      </div>
      <div style={{position: 'absolute', left: 102, right: 102, top: 910, display: 'flex', gap: 16, opacity: split}}>
        <div style={{flex: 1, background: C.red, color: C.white, padding: 24, fontSize: 30, fontWeight: 900}}>AUTOS ↓</div>
        <div style={{flex: 1, background: C.teal, color: C.white, padding: 24, fontSize: 30, fontWeight: 900}}>CLOTHING ↑</div>
      </div>
      <Brand dark/><Source dark>Retail context: Carol M. Highsmith Archive, Library of Congress • no known restrictions</Source>
    </AbsoluteFill>
  );
};

const Bars: React.FC = () => {
  const frame = useCurrentFrame();
  const rows: Array<[string, number]> = [['Autos & parts', -1.8], ['Nonstore', -2.2], ['Clothing', 1.9], ['Food services', 0.5]];
  const negativeFocus = interpolate(frame, [82, 108], [0, 1], clamp);
  const positiveFocus = interpolate(frame, [145, 171], [0, 1], clamp);
  return (
    <Shell bg={C.white}>
      <Kicker>Category tape</Kicker><Head size={70}>The categories split.</Head>
      <div style={{marginTop: 64, display: 'grid', gap: 34}}>
        {rows.map(([label, value], index) => {
          const p = spring({frame: frame - index * 15 - 8, fps: 30, config: {damping: 20}});
          const isNegative = value < 0;
          const focus = isNegative ? negativeFocus : positiveFocus;
          return (
            <div key={label} style={{display: 'grid', gridTemplateColumns: '270px 1fr 115px', alignItems: 'center', gap: 22, fontSize: 29, fontWeight: 850, opacity: 0.42 + 0.58 * Math.max(p, focus)}}>
              <span>{label}</span>
              <div style={{height: 30, background: '#e4e6e2', position: 'relative'}}>
                <div style={{height: '100%', width: `${Math.abs(value) / 2.2 * 100 * p}%`, background: isNegative ? C.red : C.teal, marginLeft: isNegative ? 'auto' : 0}}/>
              </div>
              <span style={{color: isNegative ? C.red : C.teal, textAlign: 'right'}}>{value > 0 ? '+' : ''}{value.toFixed(1)}%</span>
            </div>
          );
        })}
      </div>
      <div style={{marginTop: 66, padding: '25px 28px', background: positiveFocus > 0.5 ? '#dff3ef' : '#fde4df', fontSize: 31, fontWeight: 900}}>
        {positiveFocus > 0.5 ? 'Offsets exist. They do not erase the decline.' : 'Autos and online retail lead the downside.'}
      </div>
      <Source>Seasonally adjusted monthly changes • Census July 2026 advance release</Source>
    </Shell>
  );
};

const Document: React.FC = () => {
  const frame = useCurrentFrame();
  const documentIn = spring({frame: frame - 5, fps: 30, config: {damping: 22}});
  const bound = spring({frame: frame - 55, fps: 30, config: {damping: 18}});
  const extraction = spring({frame: frame - 120, fps: 30, config: {damping: 19}});
  return (
    <Shell bg="#e9edf0">
      <Kicker color={C.blue}>Primary document</Kicker>
      <div style={{position: 'absolute', left: 70, top: 300, width: 940, filter: 'drop-shadow(0 18px 38px rgba(16,33,43,.16))', opacity: documentIn, transform: `translateY(${(1 - documentIn) * 28}px)`}}>
        <Img src={staticFile('assets/census-document.png')} style={{width: '100%', height: 'auto', display: 'block'}}/>
      </div>
      <div style={{position: 'absolute', left: 92, top: 246, background: C.navy, color: C.white, padding: '12px 18px', fontSize: 19, fontWeight: 900, letterSpacing: 1.5, opacity: bound}}>MEASURED TEXT BINDING</div>
      <div style={{position: 'absolute', right: 84, top: 1480, width: 440, padding: '18px 22px', background: C.blue, color: C.white, fontSize: 25, fontWeight: 900, opacity: extraction, transform: `translateX(${(1 - extraction) * 35}px)`}}>Headline metrics extracted below the exact methodology text.</div>
      <Source>Official Census release text • exact-source derivative • annotation from measured target geometry</Source>
    </Shell>
  );
};

const Nominal: React.FC = () => {
  const frame = useCurrentFrame();
  const label = spring({frame: frame - 5, fps: 30, config: {damping: 20}});
  const quantity = spring({frame: frame - 70, fps: 30, config: {damping: 20}});
  const price = spring({frame: frame - 116, fps: 30, config: {damping: 20}});
  return (
    <Shell bg="#f9e9cf">
      <Kicker color={C.gold}>What the headline misses</Kicker>
      <div style={{opacity: label}}><Head size={83}>The print is nominal.</Head></div>
      <div style={{marginTop: 95, display: 'flex', gap: 24}}>
        <div style={{flex: 1, background: C.white, padding: '42px 30px', borderTop: `10px solid ${C.red}`, opacity: quantity, transform: `translateX(${(1 - quantity) * -35}px)`}}><div style={{fontSize: 45, fontWeight: 950}}>Quantity</div><div style={{fontSize: 27, color: C.muted, marginTop: 18}}>Did shoppers buy less?</div></div>
        <div style={{flex: 1, background: C.white, padding: '42px 30px', borderTop: `10px solid ${C.blue}`, opacity: price, transform: `translateX(${(1 - price) * 35}px)`}}><div style={{fontSize: 45, fontWeight: 950}}>Price</div><div style={{fontSize: 27, color: C.muted, marginTop: 18}}>Did prices fall?</div></div>
      </div>
      <div style={{fontSize: 36, lineHeight: 1.25, marginTop: 70, fontWeight: 850, opacity: price}}>The headline alone cannot separate them.</div>
      <Source>Census methodology: not adjusted for price changes</Source>
    </Shell>
  );
};

const Chain: React.FC = () => {
  const frame = useCurrentFrame();
  const nodes = ['Retail revenue', 'Inventory decisions', 'Real-consumption read'];
  return (
    <Shell bg="#dff3ef">
      <Kicker color={C.teal}>Transmission</Kicker><Head size={75}>One distinction travels.</Head>
      <div style={{marginTop: 88}}>
        {nodes.map((node, index) => {
          const p = spring({frame: frame - index * 48 - 8, fps: 30, config: {damping: 19}});
          return <React.Fragment key={node}><div style={{padding: '31px 34px', fontSize: 40, fontWeight: 900, background: index === 0 ? C.teal : C.white, color: index === 0 ? C.white : C.ink, opacity: p, transform: `translateX(${(1 - p) * 55}px)`}}>{node}</div>{index < nodes.length - 1 && <div style={{fontSize: 43, color: C.teal, margin: '6px 0 6px 44px', opacity: p}}>↓</div>}</React.Fragment>;
        })}
      </div>
      <Source>Capital Chronicle analysis • no proprietary numeric conclusion</Source>
    </Shell>
  );
};

const Wit: React.FC = () => {
  const frame = useCurrentFrame();
  const first = spring({frame: frame - 5, fps: 30, config: {damping: 20}});
  const second = spring({frame: frame - 62, fps: 30, config: {damping: 20}});
  const divider = interpolate(frame, [45, 95], [0, 700], clamp);
  return (
    <Shell bg={C.navy} color={C.white}>
      <Kicker>Market note</Kicker>
      <div style={{opacity: first, marginTop: 80}}><Head size={96} color={C.white}>One decimal gets the alert.</Head></div>
      <div style={{height: 7, width: divider, background: C.red, marginTop: 62}}/>
      <div style={{fontSize: 61, lineHeight: 1.05, fontWeight: 900, color: '#b9ccd4', marginTop: 58, opacity: second}}>Seven pages decide what it means.</div>
      <Source dark>Advance surveys are revised; confidence intervals and methods matter.</Source>
    </Shell>
  );
};

const Checkpoint: React.FC = () => {
  const frame = useCurrentFrame();
  const items = ['Revisions', 'Category breadth', 'Inflation-adjusted consumption'];
  const date = spring({frame: frame - 168, fps: 30, config: {damping: 19}});
  const thesis = spring({frame: frame - 225, fps: 30, config: {damping: 18}});
  return (
    <Shell bg={C.white}>
      <Kicker color={C.blue}>Next checkpoint</Kicker><Head size={77}>Watch three things.</Head>
      <div style={{marginTop: 72, display: 'grid', gap: 28}}>
        {items.map((item, index) => <Enter delay={index * 40 + 10} key={item}><div style={{fontSize: 39, fontWeight: 900, padding: '29px 33px', background: index === 2 ? '#f9e9cf' : '#e9f0f8', borderLeft: `9px solid ${index === 2 ? C.gold : C.blue}`}}>{String(index + 1).padStart(2, '0')} &nbsp; {item}</div></Enter>)}
      </div>
      <div style={{marginTop: 58, padding: '32px 36px', background: C.navy, color: C.white, opacity: date}}><div style={{fontSize: 23, color: '#b9ccd4'}}>NEXT ADVANCE REPORT</div><div style={{fontSize: 52, fontWeight: 950}}>SEP 16 • 8:30 ET</div></div>
      <div style={{fontSize: 36, fontWeight: 900, marginTop: 38, color: C.red, opacity: thesis}}>One soft month is a signal—not a verdict.</div>
      <Source>Scheduled by U.S. Census Bureau</Source>
    </Shell>
  );
};

const Resolve: React.FC = () => (
  <Shell bg={C.navy} color={C.white}>
    <div style={{marginTop: 430}}><Kicker>Capital Chronicle</Kicker><Head size={83} color={C.white}>Fast on the event.<br/>Slow on the conclusion.</Head></div>
    <Source dark>Research, not investment advice.</Source>
  </Shell>
);

const scenes = [Alert, WhatHit, Bars, Document, Nominal, Chain, Wit, Checkpoint, Resolve];
export const BreakingRetailSales: React.FC<BreakingProps> = ({segments}) => {
  let cursor = 0;
  return (
    <AbsoluteFill>
      {segments.map((segment, index) => {
        const Scene = scenes[Math.min(index, scenes.length - 1)];
        const from = cursor;
        cursor += segment.frames;
        return <Sequence key={segment.id} from={from} durationInFrames={segment.frames} premountFor={15}><Scene/></Sequence>;
      })}
    </AbsoluteFill>
  );
};
