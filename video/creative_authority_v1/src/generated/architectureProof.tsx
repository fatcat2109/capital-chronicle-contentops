import React from 'react';
import {AbsoluteFill, Img, Sequence, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ProofProps} from '../root';
import {
  BRAND,
  BrandBug,
  DarkFrame,
  DocumentaryImage,
  EditorialCaption,
  Eyebrow,
  GridTexture,
  NumberTag,
  Rule,
  SafeText,
  SceneIn,
  SourceAttribution,
  asset,
  clamp,
} from '../lowLevel';

// Viewer-facing architecture proof authored in this Codex task session.
// This is intentionally story-specific source, not a JSON packet feeding a fixed compositor.

const W = 1080;
const H = 1920;

const ShortHook: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const slash = interpolate(frame, [8, 36], [0, 1], clamp);
  const question = interpolate(frame, [44, 64], [0, 1], clamp);
  return (
    <AbsoluteFill style={{background: BRAND.navy, overflow: 'hidden'}}>
      <DocumentaryImage name="nasa-persian-gulf-iss069-e-92132.jpg" position="51% 54%" scaleFrom={1.03} scaleTo={1.12} />
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(3,9,14,.06), rgba(3,9,14,.14) 42%, rgba(3,9,14,.96) 86%)'}} />
      <div style={{position: 'absolute', left: 54, right: 54, bottom: 238}}>
        <Eyebrow portrait>OIL · BENCHMARK SNAPSHOT · JUL 2026</Eyebrow>
        <div style={{display: 'flex', gap: 16, alignItems: 'center', marginTop: 18}}>
          <SafeText size={88} lineHeight={.92}>TANKERS<br/>MOVED.</SafeText>
          <div style={{width: 5, height: 166 * slash, background: BRAND.copper}} />
          <SafeText size={88} lineHeight={.92} color={BRAND.teal} style={{opacity: question}}>BARRELS?</SafeText>
        </div>
      </div>
      <BrandBug portrait />
      <EditorialCaption portrait visible={captionsVisible}>Traffic returned. The harder question is whether supply did.</EditorialCaption>
      <SourceAttribution portrait>NASA astronaut photograph ISS069-E-92132 · Geographic context</SourceAttribution>
    </AbsoluteFill>
  );
};

const ShortMovement: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const split = interpolate(frame, [12, 42], [H, 930], clamp);
  const arrow = interpolate(frame, [34, 70], [0, 1], clamp);
  return (
    <AbsoluteFill style={{background: BRAND.navy, overflow: 'hidden'}}>
      <div style={{position: 'absolute', inset: 0, height: split, overflow: 'hidden'}}>
        <Img data-render-asset="eia-hormuz-map-portrait.png" src={asset('eia-hormuz-map-portrait.png')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: split, bottom: 0, overflow: 'hidden', borderTop: `5px solid ${BRAND.teal}`}}>
        <DocumentaryImage name="usns-oiler-strait-of-hormuz.jpg" position="50% 48%" scaleFrom={1.02} scaleTo={1.08} />
        <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(4,11,17,.08), rgba(4,11,17,.86))'}} />
      </div>
      <div style={{position: 'absolute', left: 48, right: 48, top: 58, padding: '18px 22px', background: 'rgba(6,16,25,.92)'}}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <Eyebrow portrait>EIA REPORTED MORE HORMUZ TRAFFIC</Eyebrow>
          <SafeText size={25} color={BRAND.copper}>AFTER JUN 18</SafeText>
        </div>
      </div>
      <div style={{position: 'absolute', left: 54, right: 54, bottom: 180}}>
        <SafeText size={68} lineHeight={.98}>MOVEMENT <span style={{color: BRAND.teal}}>IS VISIBLE.</span></SafeText>
        <div style={{height: 4, width: `${arrow * 100}%`, background: `linear-gradient(90deg, ${BRAND.teal}, ${BRAND.copper})`, margin: '20px 0'}} />
        <SafeText size={45} lineHeight={1.02} color={BRAND.copper}>RESTORED SUPPLY IS NOT.</SafeText>
      </div>
      <EditorialCaption portrait visible={captionsVisible}>EIA reported more traffic after the June eighteenth memorandum.</EditorialCaption>
      <SourceAttribution portrait>Map: U.S. EIA · Vessel: U.S. Navy, public domain</SourceAttribution>
    </AbsoluteFill>
  );
};

const ShortPhysicalChain: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const states = [
    {n: '01', label: 'UNLOAD', image: 'doe-tanker-terminal-pipeline.jpg', note: 'terminal'},
    {n: '02', label: 'RESTORE', image: 'nara-refinery-portrait.jpg', note: 'production'},
    {n: '03', label: 'REBUILD', image: 'refinery-storage-tanks.jpg', note: 'inventories'},
  ];
  return (
    <DarkFrame portrait padding="76px 44px 126px">
      <Eyebrow portrait color={BRAND.copper}>THE PHYSICAL SCHEDULE</Eyebrow>
      <SafeText size={58} lineHeight={.98} style={{marginTop: 18}}>A SHIP IS ONLY<br/><span style={{color: BRAND.teal}}>STEP ONE.</span></SafeText>
      <div style={{display: 'grid', gridTemplateRows: 'repeat(3, 1fr)', gap: 14, flex: 1, marginTop: 30, minHeight: 0}}>
        {states.map((state, index) => {
          const visible = interpolate(frame, [10 + index * 28, 30 + index * 28], [0, 1], clamp);
          const active = frame > 18 + index * 28;
          return (
            <div key={state.label} style={{position: 'relative', minHeight: 0, overflow: 'hidden', opacity: visible, transform: `translateX(${(1 - visible) * 42}px)`}}>
              <DocumentaryImage name={state.image} position={state.label === 'RESTORE' ? '50% 52%' : 'center'} scaleFrom={1.01} scaleTo={1.05} />
              <AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(4,11,17,.92), rgba(4,11,17,.18) 72%)'}} />
              <div style={{position: 'absolute', left: 22, top: 20, display: 'flex', alignItems: 'center', gap: 18}}>
                <NumberTag color={active ? BRAND.teal : BRAND.copper}>{state.n}</NumberTag>
                <div>
                  <SafeText size={42}>{state.label}</SafeText>
                  <SafeText size={21} color={BRAND.muted} tracking={.06}>{state.note.toUpperCase()}</SafeText>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <EditorialCaption portrait visible={captionsVisible}>The oil still has to unload, production must return, and inventories must rebuild.</EditorialCaption>
      <SourceAttribution portrait>U.S. DOE and NARA public-domain imagery · Storage: Tony Webster, CC BY 4.0</SourceAttribution>
    </DarkFrame>
  );
};

const ShortDocument: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const verdict = interpolate(frame, [40, 62], [0, 1], clamp);
  return (
    <AbsoluteFill style={{background: '#ebe8df', overflow: 'hidden'}}>
      <div style={{position: 'absolute', inset: 0, transform: 'translateY(110px) scale(.96)'}}>
        <Img data-render-asset="eia-release-document-portrait.png" src={asset('eia-release-document-portrait.png')} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: 230, background: BRAND.navy, padding: '52px 54px'}}>
        <Eyebrow portrait color={BRAND.copper}>PRIMARY EVIDENCE · JUL 7, 2026</Eyebrow>
        <SafeText size={54} style={{marginTop: 18}}>THE SOURCE GOES FIRST.</SafeText>
      </div>
      <div style={{position: 'absolute', left: 54, right: 54, bottom: 118, padding: '26px 30px', background: BRAND.navy, borderTop: `5px solid ${BRAND.copper}`, opacity: verdict}}>
        <SafeText size={42} color={BRAND.copper}>FORECAST</SafeText>
        <SafeText size={28} color={BRAND.ink} style={{marginTop: 6}}>Not a result. Not a certainty.</SafeText>
      </div>
      <EditorialCaption portrait visible={captionsVisible}>This is EIA's July seventh release. Forward values are forecasts.</EditorialCaption>
      <SourceAttribution portrait dark={false}>U.S. Energy Information Administration · Release date preserved</SourceAttribution>
    </AbsoluteFill>
  );
};

const PricePathChart: React.FC<{portrait?: boolean}> = ({portrait = false}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const progress = interpolate(frame, [16, durationInFrames - 24], [0, 1], clamp);
  const width = portrait ? 890 : 1040;
  const height = portrait ? 750 : 490;
  const x = [70, width * .52, width - 70];
  const y = [80, height * .55, height - 84];
  const path = `M ${x[0]} ${y[0]} L ${x[1]} ${y[1]} L ${x[2]} ${y[2]}`;
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <defs>
        <linearGradient id="forecastLine" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={BRAND.ink}/><stop offset=".35" stopColor={BRAND.teal}/><stop offset="1" stopColor={BRAND.copper}/>
        </linearGradient>
      </defs>
      {[.2,.4,.6,.8].map((p) => <line key={p} x1="0" x2={width} y1={height*p} y2={height*p} stroke={BRAND.line} strokeWidth="1" />)}
      <path d={path} pathLength="1" stroke="url(#forecastLine)" strokeWidth={portrait ? 8 : 6} fill="none" strokeDasharray="1" strokeDashoffset={1-progress} />
      {[
        {value: '$85', sub: 'JUNE · REFERENCE', color: BRAND.ink},
        {value: '$74', sub: 'Q3 · FORECAST', color: BRAND.teal},
        {value: '$65', sub: '2027 · FORECAST', color: BRAND.copper},
      ].map((point, index) => {
        const shown = progress > index * .42 - .02;
        return (
          <g key={point.value} opacity={shown ? 1 : 0}>
            <circle cx={x[index]} cy={y[index]} r={portrait ? 13 : 10} fill={point.color}/>
            <text x={x[index]} y={y[index]-34} textAnchor={index === 0 ? 'start' : index === 2 ? 'end' : 'middle'} fill={point.color} fontFamily="Arial" fontWeight="900" fontSize={portrait ? 62 : 48}>{point.value}</text>
            <text x={x[index]} y={y[index]+48} textAnchor={index === 0 ? 'start' : index === 2 ? 'end' : 'middle'} fill={BRAND.muted} fontFamily="Arial" fontWeight="800" fontSize={portrait ? 27 : 22}>{point.sub}</text>
          </g>
        );
      })}
    </svg>
  );
};

const ShortForecast: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => (
  <DarkFrame portrait>
    <GridTexture />
    <Eyebrow portrait>EIA BRENT PATH · REFERENCE VS FORECAST</Eyebrow>
    <SafeText size={60} lineHeight={.98} style={{marginTop: 18}}>THE LINE SLOPES DOWN.<br/><span style={{color: BRAND.copper}}>THE EVIDENCE ISN'T FINISHED.</span></SafeText>
    <div style={{display: 'grid', placeItems: 'center', flex: 1}}><PricePathChart portrait /></div>
    <div style={{padding: '18px 22px', borderLeft: `5px solid ${BRAND.teal}`, background: 'rgba(16,34,48,.86)'}}>
      <SafeText size={27} color={BRAND.ink}>Observation and forecast stay visually distinct.</SafeText>
    </div>
    <EditorialCaption portrait visible={captionsVisible}>June Brent was eighty-five dollars. EIA forecast seventy-four in Q3 and sixty-five in 2027.</EditorialCaption>
    <SourceAttribution portrait>Data: U.S. EIA July 2026 STEO · Native chart: Capital Chronicle</SourceAttribution>
  </DarkFrame>
);

const ShortTransmission: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const columns = [
    {label: 'IMPORTERS', value: 'POSSIBLE SUPPORT', color: BRAND.teal},
    {label: 'PRODUCERS', value: 'REVENUE PRESSURE', color: BRAND.copper},
    {label: 'INFLATION', value: 'MAY EASE', color: BRAND.teal},
  ];
  return (
    <AbsoluteFill style={{background: BRAND.navy, overflow: 'hidden'}}>
      <div style={{position: 'absolute', inset: 0, display: 'grid', gridTemplateRows: '1fr 1fr'}}>
        <div style={{overflow: 'hidden'}}><DocumentaryImage name="commercial-tanker-oil-platform-persian-gulf.jpg" position="50% 55%" /></div>
        <div style={{overflow: 'hidden'}}><DocumentaryImage name="crude-oil-supertanker.jpg" position="50% 48%" scaleFrom={1.08} scaleTo={1.16} /></div>
      </div>
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(4,11,17,.28), rgba(4,11,17,.93) 42%, rgba(4,11,17,.98))'}} />
      <div style={{position: 'absolute', left: 54, right: 54, top: 76}}>
        <Eyebrow portrait color={BRAND.copper}>ANALYSIS · CONDITIONAL CHANNELS</Eyebrow>
        <SafeText size={58} lineHeight={.96} style={{marginTop: 18}}>LOWER OIL<br/><span style={{color: BRAND.teal}}>DOESN'T LAND EVENLY.</span></SafeText>
      </div>
      <div style={{position: 'absolute', left: 54, right: 54, bottom: 160, display: 'grid', gap: 12}}>
        {columns.map((column, index) => {
          const shown = interpolate(frame, [15+index*18, 32+index*18], [0,1], clamp);
          return (
            <div key={column.label} style={{display: 'grid', gridTemplateColumns: '220px 1fr', gap: 18, alignItems: 'center', padding: '18px 20px', background: 'rgba(6,16,25,.9)', borderLeft: `5px solid ${column.color}`, opacity: shown}}>
              <SafeText size={22} color={BRAND.muted} tracking={.06}>{column.label}</SafeText>
              <SafeText size={32} color={column.color}>{column.value}</SafeText>
            </div>
          );
        })}
      </div>
      <EditorialCaption portrait visible={captionsVisible}>A sustained retreat may support importers and pressure producer revenues.</EditorialCaption>
      <SourceAttribution portrait>U.S. Navy public-domain tanker imagery · Analysis: governed Capital Chronicle article</SourceAttribution>
    </AbsoluteFill>
  );
};

const ShortPolicy: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const rows = [
    ['GASOLINE', '$3.80 Q3 → $3.40 Q4', BRAND.teal],
    ['HEADLINE INFLATION', 'MAY EASE', BRAND.teal],
    ['FED POLICY', 'BROADER CONDITIONS STILL MATTER', BRAND.copper],
  ] as const;
  return (
    <AbsoluteFill style={{background: BRAND.navy, overflow: 'hidden'}}>
      <GridTexture />
      <div style={{position: 'absolute', right: -130, top: 360, width: 720, height: 720, border: `80px solid rgba(67,216,189,.06)`, borderRadius: 999}} />
      <div style={{position: 'absolute', left: 54, right: 54, top: 76}}>
        <Eyebrow portrait>THE POLICY BOUNDARY</Eyebrow>
        <SafeText size={58} lineHeight={.98} style={{marginTop: 18}}>CHEAPER GAS<br/><span style={{color: BRAND.copper}}>ISN'T A FED SWITCH.</span></SafeText>
      </div>
      <div style={{position: 'absolute', left: 54, right: 54, top: 630, display: 'grid', gap: 14}}>
        {rows.map(([label, value, color], index) => {
          const shown = interpolate(frame, [10+index*20, 28+index*20], [0,1], clamp);
          return <div key={label} style={{padding: '22px 24px', background: 'rgba(6,16,25,.9)', borderTop: `4px solid ${color}`, opacity: shown}}><SafeText size={21} color={BRAND.muted} tracking={.08}>{label}</SafeText><SafeText size={34} color={color} style={{marginTop: 7}}>{value}</SafeText></div>;
        })}
      </div>
      <EditorialCaption portrait visible={captionsVisible}>Lower gasoline can ease headline inflation, but the Fed still weighs broader conditions.</EditorialCaption>
      <SourceAttribution portrait>EIA gasoline forecast · Policy boundary: governed Capital Chronicle article</SourceAttribution>
    </AbsoluteFill>
  );
};

const TestGrid: React.FC<{portrait?: boolean}> = ({portrait = false}) => {
  const frame = useCurrentFrame();
  const groups = [
    {title: 'CONFIRM IF', color: BRAND.teal, rows: ['TRAFFIC NORMALIZES', 'PRODUCTION RETURNS', 'INVENTORIES BUILD', 'BRENT TRACKS PATH']},
    {title: 'CHALLENGE IF', color: BRAND.red, rows: ['DISRUPTION RETURNS', 'RESTARTS STALL', 'DRAWS PERSIST', 'PRICE HOLDS ABOVE PATH']},
  ];
  return (
    <div style={{display: 'grid', gridTemplateColumns: portrait ? '1fr' : '1fr 1fr', gap: portrait ? 16 : 22, width: '100%'}}>
      {groups.map((group, groupIndex) => (
        <div key={group.title} style={{background: 'rgba(6,16,25,.9)', borderTop: `5px solid ${group.color}`, padding: portrait ? '22px 24px' : '26px 30px'}}>
          <SafeText size={portrait ? 32 : 30} color={group.color}>{group.title}</SafeText>
          <div style={{display: 'grid', gap: portrait ? 10 : 12, marginTop: portrait ? 16 : 18}}>
            {group.rows.map((row, index) => {
              const shown = interpolate(frame, [8+groupIndex*16+index*7, 20+groupIndex*16+index*7], [0,1], clamp);
              return <div key={row} style={{display: 'flex', gap: 12, alignItems: 'center', opacity: shown}}><div style={{width: 8, height: 8, borderRadius: 99, background: group.color}}/><SafeText size={portrait ? 23 : 22} color={BRAND.ink} tracking={.01}>{row}</SafeText></div>;
            })}
          </div>
        </div>
      ))}
    </div>
  );
};

const ShortTest: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => (
  <AbsoluteFill style={{background: BRAND.navy, overflow: 'hidden'}}>
    <Img data-render-asset="eia-hormuz-map-landscape.png" src={asset('eia-hormuz-map-landscape.png')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '52% 50%'}} />
    <AbsoluteFill style={{background: 'rgba(4,11,17,.76)'}} />
    <div style={{position: 'absolute', left: 46, right: 46, top: 76}}>
      <Eyebrow portrait color={BRAND.copper}>A THESIS NEEDS AN EXIT</Eyebrow>
      <SafeText size={56} lineHeight={.98} style={{marginTop: 18}}>WHAT WOULD<br/><span style={{color: BRAND.teal}}>PROVE IT WRONG?</span></SafeText>
    </div>
    <div style={{position: 'absolute', left: 46, right: 46, top: 500}}><TestGrid portrait /></div>
    <EditorialCaption portrait visible={captionsVisible}>Confirm it with traffic, production, inventories and Brent. Challenge it if those signals reverse.</EditorialCaption>
    <SourceAttribution portrait>Conditions: governed Capital Chronicle analysis · Map: U.S. EIA</SourceAttribution>
  </AbsoluteFill>
);

const ShortResolve: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const line = interpolate(frame, [10, 48], [0, 1], clamp);
  return (
    <DarkFrame portrait>
      <GridTexture />
      <Eyebrow portrait color={BRAND.copper}>BENCHMARK SNAPSHOT · OBSERVATION ≠ FORECAST</Eyebrow>
      <div style={{marginTop: 120}}>
        <SafeText size={84}>$69.60</SafeText>
        <SafeText size={25} color={BRAND.muted} tracking={.08}>WTI · JUL 6 OBSERVATION</SafeText>
      </div>
      <div style={{position: 'absolute', left: 54, right: 54, top: 780}}>
        <div style={{height: 5, width: `${line*100}%`, background: `linear-gradient(90deg, ${BRAND.teal}, ${BRAND.copper})`}} />
        <div style={{display: 'flex', justifyContent: 'space-between', marginTop: 24}}>
          <SafeText size={32}>JUL 15</SafeText><SafeText size={32}>AUG 11</SafeText>
        </div>
        <SafeText size={25} color={BRAND.muted} style={{marginTop: 36}}>At the July benchmark snapshot, these were the next EIA checkpoints—not promised outcomes.</SafeText>
      </div>
      <div style={{position: 'absolute', left: 54, bottom: 220}}>
        <SafeText size={52}>MARKETS CAN PRICE THE PATH.</SafeText>
        <SafeText size={52} color={BRAND.teal}>TANKS STILL HAVE TO FILL.</SafeText>
        <Rule width={220} color={BRAND.copper}/>
      </div>
      <EditorialCaption portrait visible={captionsVisible}>WTI was a separate observation. The next checkpoint was not a promised outcome.</EditorialCaption>
      <SourceAttribution portrait>WTI: FRED DCOILWTICO · Checkpoints and Brent forecast: U.S. EIA</SourceAttribution>
    </DarkFrame>
  );
};

const shortDurations = [90, 150, 210, 210, 240, 180, 210, 180, 150];
export const SHORT_FRAMES = shortDurations.reduce((sum, value) => sum + value, 0);

export const ArchitectureProofShort: React.FC<ProofProps> = ({captionsVisible}) => {
  const scenes: React.ReactNode[] = [
    <ShortHook key="hook" captionsVisible={captionsVisible}/>,
    <ShortMovement key="movement" captionsVisible={captionsVisible}/>,
    <ShortPhysicalChain key="chain" captionsVisible={captionsVisible}/>,
    <ShortDocument key="document" captionsVisible={captionsVisible}/>,
    <ShortForecast key="forecast" captionsVisible={captionsVisible}/>,
    <ShortTransmission key="transmission" captionsVisible={captionsVisible}/>,
    <ShortPolicy key="policy" captionsVisible={captionsVisible}/>,
    <ShortTest key="test" captionsVisible={captionsVisible}/>,
    <ShortResolve key="resolve" captionsVisible={captionsVisible}/>,
  ];
  let from = 0;
  return <AbsoluteFill style={{background: BRAND.navy}}>{scenes.map((scene, index) => {const start = from; from += shortDurations[index]; return <Sequence key={index} from={start} durationInFrames={shortDurations[index]}>{scene}</Sequence>;})}</AbsoluteFill>;
};

const MidOpening: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const reveal = interpolate(frame, [4, 20], [0, 1], clamp);
  return (
    <AbsoluteFill style={{background: BRAND.navy, overflow: 'hidden'}}>
      <DocumentaryImage name="nasa-persian-gulf-iss069-e-92132.jpg" position="52% 50%" scaleFrom={1.02} scaleTo={1.1}/>
      <AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(3,9,14,.94), rgba(3,9,14,.46) 56%, rgba(3,9,14,.08))'}}/>
      <div style={{position: 'absolute', left: 74, top: 270, width: 960, opacity: reveal}}>
        <Eyebrow color={BRAND.copper}>EIA / HORMUZ · ARCHITECTURE PROOF</Eyebrow>
        <SafeText size={78} lineHeight={.94} style={{marginTop: 20}}>THE SHIPS MOVED.<br/><span style={{color: BRAND.teal}}>DID SUPPLY?</span></SafeText>
        <SafeText size={27} color={BRAND.muted} maxWidth={700} style={{marginTop: 28}}>A physical-chain test of one oil-market forecast.</SafeText>
      </div>
      <BrandBug/>
      <EditorialCaption visible={captionsVisible}>Traffic is visible. Supply recovery still has several tests.</EditorialCaption>
      <SourceAttribution>NASA astronaut photograph ISS069-E-92132 · Geographic context</SourceAttribution>
    </AbsoluteFill>
  );
};

const MidMapVessel: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const split = interpolate(frame, [20, 62], [86, 49], clamp);
  return (
    <AbsoluteFill style={{background: BRAND.navy, overflow: 'hidden'}}>
      <div style={{position: 'absolute', inset: 0, right: `${100-split}%`, overflow: 'hidden'}}>
        <Img data-render-asset="eia-hormuz-map-landscape.png" src={asset('eia-hormuz-map-landscape.png')} style={{width: '100%', height: '100%', objectFit: 'cover'}}/>
      </div>
      <div style={{position: 'absolute', left: `${split}%`, right: 0, top: 0, bottom: 0, overflow: 'hidden', borderLeft: `5px solid ${BRAND.teal}`}}>
        <DocumentaryImage name="usns-oiler-strait-of-hormuz.jpg" position="52% 50%"/>
      </div>
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(3,9,14,.08), rgba(3,9,14,.82) 90%)'}}/>
      <div style={{position: 'absolute', left: 72, right: 72, bottom: 116}}>
        <SafeText size={56}>GEOGRAPHY EXPLAINS THE <span style={{color: BRAND.teal}}>CHOKEPOINT.</span></SafeText>
        <SafeText size={31} color={BRAND.copper} style={{marginTop: 10}}>It does not prove the barrels arrived.</SafeText>
      </div>
      <EditorialCaption visible={captionsVisible}>EIA reported increased Hormuz traffic after the June eighteenth memorandum.</EditorialCaption>
      <SourceAttribution>Map: U.S. EIA · Vessel: U.S. Navy, public domain</SourceAttribution>
    </AbsoluteFill>
  );
};

const MidPhysical: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const rows = [
    {label: 'UNLOAD', sub: 'terminal', image: 'doe-tanker-terminal-pipeline.jpg'},
    {label: 'RESTORE', sub: 'production', image: 'nara-refinery-portrait.jpg'},
    {label: 'REBUILD', sub: 'inventories', image: 'refinery-storage-tanks.jpg'},
  ];
  return (
    <DarkFrame>
      <Eyebrow color={BRAND.copper}>THE PHYSICAL CHAIN</Eyebrow>
      <SafeText size={58} style={{marginTop: 15}}>MOVEMENT HAS TO BECOME <span style={{color: BRAND.teal}}>AVAILABLE SUPPLY.</span></SafeText>
      <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 18, flex: 1, marginTop: 34, minHeight: 0}}>
        {rows.map((row,index) => {
          const shown = interpolate(frame, [10+index*20, 32+index*20], [0,1], clamp);
          return <div key={row.label} style={{position: 'relative', overflow: 'hidden', opacity: shown, transform: `translateY(${(1-shown)*34}px)`}}><DocumentaryImage name={row.image} position={row.label==='RESTORE'?'50% 45%':'center'}/><AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(4,11,17,.05), rgba(4,11,17,.9))'}}/><div style={{position:'absolute',left:24,bottom:28}}><SafeText size={44}>{row.label}</SafeText><SafeText size={19} color={BRAND.teal} tracking={.08}>{row.sub.toUpperCase()}</SafeText></div></div>;
        })}
      </div>
      <EditorialCaption visible={captionsVisible}>Supply recovery requires unloading, restored production, and rebuilding inventories.</EditorialCaption>
      <SourceAttribution>U.S. DOE and NARA public-domain imagery · Storage: Tony Webster, CC BY 4.0</SourceAttribution>
    </DarkFrame>
  );
};

const MidTransitLimit: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => (
  <AbsoluteFill style={{background: BRAND.navy, overflow: 'hidden'}}>
    <DocumentaryImage name="commercial-tanker-oil-platform-persian-gulf.jpg" position="58% 48%"/>
    <AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(3,9,14,.95), rgba(3,9,14,.46) 64%, rgba(3,9,14,.1))'}}/>
    <div style={{position:'absolute',left:74,top:245,width:890}}>
      <Eyebrow color={BRAND.copper}>NECESSARY ≠ SUFFICIENT</Eyebrow>
      <SafeText size={72} lineHeight={.96} style={{marginTop:18}}>PAST THE STRAIT.<br/><span style={{color:BRAND.teal}}>NOT YET IN INVENTORY.</span></SafeText>
      <Rule width={250}/>
    </div>
    <EditorialCaption visible={captionsVisible}>Transit establishes movement, not production restoration or inventory growth.</EditorialCaption>
    <SourceAttribution>U.S. Navy public-domain photograph · Mechanism: governed Capital Chronicle article</SourceAttribution>
  </AbsoluteFill>
);

const MidEvidence: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const push = interpolate(frame,[0,360],[1,1.06],clamp);
  return (
    <AbsoluteFill style={{background:BRAND.navy,overflow:'hidden'}}>
      <div style={{position:'absolute',left:720,top:48,width:1130,height:950,background:'#ebe8df',overflow:'hidden'}}>
        <Img data-render-asset="eia-release-document-landscape.png" src={asset('eia-release-document-landscape.png')} style={{width:'100%',height:'100%',objectFit:'contain',transform:`scale(${push})`}}/>
      </div>
      <div style={{position:'absolute',left:72,top:160,width:560}}>
        <Eyebrow color={BRAND.copper}>SOURCE ON RECORD · JUL 7, 2026</Eyebrow>
        <SafeText size={66} lineHeight={.96} style={{marginTop:22}}>FORECAST.<br/><span style={{color:BRAND.teal}}>NOT A RESULT.</span></SafeText>
        <SafeText size={28} color={BRAND.muted} style={{marginTop:30}}>The date, source identity and forecast boundary remain visible before interpretation.</SafeText>
      </div>
      <EditorialCaption visible={captionsVisible}>EIA expected flows and prices to move toward pre-conflict conditions.</EditorialCaption>
      <SourceAttribution>U.S. Energy Information Administration · July 7, 2026</SourceAttribution>
    </AbsoluteFill>
  );
};

const MidForecast: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => (
  <DarkFrame>
    <GridTexture/>
    <div style={{display:'grid',gridTemplateColumns:'650px 1fr',gap:70,alignItems:'center',height:'100%'}}>
      <div>
        <Eyebrow>BRENT · REFERENCE VS FORECAST</Eyebrow>
        <SafeText size={66} lineHeight={.95} style={{marginTop:20}}>A DECLINING PATH.<br/><span style={{color:BRAND.copper}}>A CONDITIONAL OUTCOME.</span></SafeText>
        <SafeText size={27} color={BRAND.muted} style={{marginTop:28}}>June is the reference. Q3 and 2027 are EIA forecasts.</SafeText>
      </div>
      <div style={{display:'grid',placeItems:'center'}}><PricePathChart/></div>
    </div>
    <EditorialCaption visible={captionsVisible}>June Brent was eighty-five dollars. EIA forecast seventy-four in Q3 and sixty-five in 2027.</EditorialCaption>
    <SourceAttribution>Data: U.S. EIA July 2026 STEO · Native chart: Capital Chronicle</SourceAttribution>
  </DarkFrame>
);

const MidBalanceSheet: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame=useCurrentFrame();
  const cards=[
    {title:'IMPORTERS',body:'Possible current-account and inflation relief',color:BRAND.teal},
    {title:'PRODUCERS',body:'Possible revenue and fiscal pressure',color:BRAND.copper},
  ];
  return (
    <AbsoluteFill style={{background:BRAND.navy,overflow:'hidden'}}>
      <div style={{position:'absolute',inset:0,display:'grid',gridTemplateColumns:'1fr 1fr'}}>
        <div style={{overflow:'hidden'}}><DocumentaryImage name="crude-oil-supertanker.jpg" position="50% 50%" scaleFrom={1.18} scaleTo={1.24}/></div>
        <div style={{overflow:'hidden'}}><DocumentaryImage name="refinery-storage-tanks.jpg" position="50% 48%"/></div>
      </div>
      <AbsoluteFill style={{background:'linear-gradient(180deg,rgba(4,11,17,.32),rgba(4,11,17,.9) 72%)'}}/>
      <div style={{position:'absolute',left:72,top:70}}><Eyebrow color={BRAND.copper}>SECOND-ORDER TRANSMISSION</Eyebrow><SafeText size={60} style={{marginTop:16}}>THE SAME PRICE MOVE HITS <span style={{color:BRAND.teal}}>DIFFERENT BALANCE SHEETS.</span></SafeText></div>
      <div style={{position:'absolute',left:72,right:72,bottom:110,display:'grid',gridTemplateColumns:'1fr 1fr',gap:24}}>
        {cards.map((card,index)=>{const shown=interpolate(frame,[15+index*24,38+index*24],[0,1],clamp);return <div key={card.title} style={{padding:'28px 32px',background:'rgba(6,16,25,.92)',borderTop:`5px solid ${card.color}`,opacity:shown}}><SafeText size={24} color={card.color} tracking={.08}>{card.title}</SafeText><SafeText size={34} style={{marginTop:10}}>{card.body}</SafeText></div>;})}
      </div>
      <EditorialCaption visible={captionsVisible}>A sustained retreat can support importers while pressuring producer revenues.</EditorialCaption>
      <SourceAttribution>U.S. Navy public-domain tanker · Storage: Tony Webster, CC BY 4.0</SourceAttribution>
    </AbsoluteFill>
  );
};

const MidGasoline: React.FC<{captionsVisible:boolean}> = ({captionsVisible}) => {
  const frame=useCurrentFrame();
  return (
    <AbsoluteFill style={{background:BRAND.navy,overflow:'hidden'}}>
      <div style={{position:'absolute',left:0,top:0,bottom:0,width:760,overflow:'hidden'}}><DocumentaryImage name="nara-refinery-portrait.jpg" position="50% 48%"/></div>
      <div style={{position:'absolute',left:760,right:0,top:0,bottom:0,padding:'95px 80px',background:'#0b1a25'}}>
        <Eyebrow color={BRAND.copper}>GASOLINE FORECAST</Eyebrow>
        <div style={{display:'flex',alignItems:'baseline',gap:24,marginTop:38}}><SafeText size={92} color={BRAND.teal}>$3.80</SafeText><SafeText size={28} color={BRAND.muted}>Q3</SafeText></div>
        <div style={{height:4,width:`${interpolate(frame,[16,70],[0,100],clamp)}%`,background:`linear-gradient(90deg,${BRAND.teal},${BRAND.copper})`,margin:'28px 0'}}/>
        <div style={{display:'flex',alignItems:'baseline',gap:24}}><SafeText size={92} color={BRAND.copper}>$3.40</SafeText><SafeText size={28} color={BRAND.muted}>Q4</SafeText></div>
        <SafeText size={34} style={{marginTop:46}}>Potential headline relief.<br/><span style={{color:BRAND.copper}}>Not an automatic policy move.</span></SafeText>
      </div>
      <EditorialCaption visible={captionsVisible}>EIA forecast gasoline at three eighty in Q3 and three forty in Q4.</EditorialCaption>
      <SourceAttribution>Forecast: U.S. EIA · Refinery: U.S. National Archives, public domain</SourceAttribution>
    </AbsoluteFill>
  );
};

const MidPolicy: React.FC<{captionsVisible:boolean}> = ({captionsVisible}) => (
  <AbsoluteFill style={{background:BRAND.navy,overflow:'hidden'}}>
    <DocumentaryImage name="doe-tanker-terminal-pipeline.jpg" position="50% 52%"/>
    <AbsoluteFill style={{background:'linear-gradient(90deg,rgba(4,11,17,.96),rgba(4,11,17,.75),rgba(4,11,17,.35))'}}/>
    <div style={{position:'absolute',left:78,top:170,width:980}}>
      <Eyebrow>THE MACRO BOUNDARY</Eyebrow>
      <SafeText size={72} lineHeight={.96} style={{marginTop:20}}>OIL CAN MOVE HEADLINE INFLATION.<br/><span style={{color:BRAND.copper}}>IT DOESN'T SET THE WHOLE REACTION FUNCTION.</span></SafeText>
      <SafeText size={29} color={BRAND.muted} style={{marginTop:34}}>Broader price persistence, labor conditions and inflation expectations still matter.</SafeText>
      <Rule width={290}/>
    </div>
    <EditorialCaption visible={captionsVisible}>Federal Reserve policy still depends on broader conditions.</EditorialCaption>
    <SourceAttribution>Policy boundary: governed Capital Chronicle article · Terminal: U.S. DOE, public domain</SourceAttribution>
  </AbsoluteFill>
);

const MidTest: React.FC<{captionsVisible:boolean}> = ({captionsVisible}) => (
  <DarkFrame>
    <GridTexture/>
    <div style={{display:'grid',gridTemplateColumns:'560px 1fr',gap:70,alignItems:'center',height:'100%'}}>
      <div><Eyebrow color={BRAND.copper}>CONFIRM / CHALLENGE</Eyebrow><SafeText size={65} lineHeight={.96} style={{marginTop:20}}>A FORECAST NEEDS A <span style={{color:BRAND.teal}}>FALSIFICATION TEST.</span></SafeText><SafeText size={28} color={BRAND.muted} style={{marginTop:28}}>No empty panel. Every condition is visible.</SafeText></div>
      <TestGrid/>
    </div>
    <EditorialCaption visible={captionsVisible}>Watch traffic, production, inventories and Brent together.</EditorialCaption>
    <SourceAttribution>Conditions: governed Capital Chronicle analysis · Forecast boundary: U.S. EIA</SourceAttribution>
  </DarkFrame>
);

const MidCheckpoint: React.FC<{captionsVisible:boolean}> = ({captionsVisible}) => {
  const frame=useCurrentFrame();
  const line=interpolate(frame,[10,65],[0,1],clamp);
  return (
    <DarkFrame>
      <GridTexture/>
      <div style={{display:'grid',gridTemplateColumns:'620px 1fr',gap:70,alignItems:'center',height:'100%'}}>
        <div><Eyebrow color={BRAND.copper}>BENCHMARK SNAPSHOT · JUL 2026</Eyebrow><SafeText size={86} style={{marginTop:22}}>$69.60</SafeText><SafeText size={24} color={BRAND.muted} tracking={.08}>WTI · JUL 6 OBSERVATION</SafeText><SafeText size={28} color={BRAND.muted} style={{marginTop:34}}>A separate observation. It did not prove the Brent forecast.</SafeText></div>
        <div><div style={{height:5,width:`${line*100}%`,background:`linear-gradient(90deg,${BRAND.teal},${BRAND.copper})`}}/><div style={{display:'flex',justifyContent:'space-between',marginTop:24}}><SafeText size={34}>JUL 15</SafeText><SafeText size={34}>AUG 11</SafeText></div><SafeText size={27} color={BRAND.muted} style={{marginTop:42}}>At the snapshot, these were checkpoints—not promised outcomes.</SafeText></div>
      </div>
      <EditorialCaption visible={captionsVisible}>The benchmark's next dates were checkpoints, not predictions.</EditorialCaption>
      <SourceAttribution>WTI: FRED DCOILWTICO · Checkpoints and forecast: U.S. EIA</SourceAttribution>
    </DarkFrame>
  );
};

const MidResolve: React.FC<{captionsVisible:boolean}> = ({captionsVisible}) => {
  const frame=useCurrentFrame();
  const reveal=interpolate(frame,[10,42],[0,1],clamp);
  return (
    <DarkFrame style={{display:'grid',placeItems:'center'}}>
      <GridTexture/>
      <div style={{textAlign:'center',opacity:reveal}}>
        <SafeText size={72} align="center">MARKETS CAN PRICE THE PATH.</SafeText>
        <SafeText size={72} align="center" color={BRAND.teal}>THE PHYSICAL CHAIN GETS A VOTE.</SafeText>
        <div style={{width:240,height:5,background:BRAND.copper,margin:'34px auto'}}/>
        <SafeText size={27} align="center" color={BRAND.muted}>Truth first. Analysis second. Engagement never rewrites either.</SafeText>
        <SafeText size={30} align="center" style={{marginTop:70}}>CAPITAL <span style={{color:BRAND.teal}}>CHRONICLE</span></SafeText>
      </div>
      <EditorialCaption visible={captionsVisible}>The forecast is a path. The physical evidence decides whether it holds.</EditorialCaption>
      <SourceAttribution>Architecture proof only · No public write authority</SourceAttribution>
    </DarkFrame>
  );
};

const midDurations=[150,240,300,240,360,300,300,300,300,300,210,180];
export const MIDFORM_FRAMES=midDurations.reduce((sum,value)=>sum+value,0);

export const ArchitectureProofMidform:React.FC<ProofProps>=({captionsVisible})=>{
  const scenes:React.ReactNode[]=[
    <MidOpening key="opening" captionsVisible={captionsVisible}/>,
    <MidMapVessel key="map" captionsVisible={captionsVisible}/>,
    <MidPhysical key="physical" captionsVisible={captionsVisible}/>,
    <MidTransitLimit key="transit" captionsVisible={captionsVisible}/>,
    <MidEvidence key="evidence" captionsVisible={captionsVisible}/>,
    <MidForecast key="forecast" captionsVisible={captionsVisible}/>,
    <MidBalanceSheet key="balance" captionsVisible={captionsVisible}/>,
    <MidGasoline key="gasoline" captionsVisible={captionsVisible}/>,
    <MidPolicy key="policy" captionsVisible={captionsVisible}/>,
    <MidTest key="test" captionsVisible={captionsVisible}/>,
    <MidCheckpoint key="checkpoint" captionsVisible={captionsVisible}/>,
    <MidResolve key="resolve" captionsVisible={captionsVisible}/>,
  ];
  let from=0;
  return <AbsoluteFill style={{background:BRAND.navy}}>{scenes.map((scene,index)=>{const start=from;from+=midDurations[index];return <Sequence key={index} from={start} durationInFrames={midDurations[index]}>{scene}</Sequence>;})}</AbsoluteFill>;
};
