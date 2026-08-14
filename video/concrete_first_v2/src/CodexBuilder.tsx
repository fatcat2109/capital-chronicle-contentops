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
import type {VariantProps} from './types';

const NAVY = '#07111c';
const INK = '#f4f7f8';
const TEAL = '#42d4bd';
const COPPER = '#d99a55';
const MUTED = '#a8b7c3';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

const asset = (name: string) => staticFile(`assets/${name}`);

const Source: React.FC<{children: React.ReactNode; portrait: boolean}> = ({children, portrait}) => (
  <div
    style={{
      position: 'absolute',
      left: portrait ? 58 : 64,
      right: portrait ? 58 : 64,
      bottom: portrait ? 48 : 28,
      color: '#d0d8df',
      fontFamily: 'Arial, sans-serif',
      fontSize: portrait ? 20 : 18,
      lineHeight: 1.25,
      textShadow: '0 2px 8px rgba(0,0,0,.95)',
      zIndex: 30,
    }}
  >
    {children}
  </div>
);

const Caption: React.FC<{children: React.ReactNode; portrait: boolean}> = ({children, portrait}) => (
  <div
    style={{
      position: 'absolute',
      left: portrait ? 54 : 170,
      right: portrait ? 54 : 170,
      bottom: portrait ? 150 : 86,
      padding: portrait ? '18px 22px' : '14px 22px',
      color: INK,
      background: 'rgba(5,12,19,.91)',
      borderLeft: `5px solid ${TEAL}`,
      fontFamily: 'Arial, sans-serif',
      fontWeight: 700,
      fontSize: portrait ? 34 : 28,
      lineHeight: 1.22,
      zIndex: 40,
    }}
  >
    {children}
  </div>
);

const Eyebrow: React.FC<{children: React.ReactNode; color?: string; portrait: boolean}> = ({
  children,
  color = TEAL,
  portrait,
}) => (
  <div
    style={{
      color,
      fontFamily: 'Arial, sans-serif',
      fontSize: portrait ? 23 : 20,
      letterSpacing: 3.2,
      fontWeight: 800,
      textTransform: 'uppercase',
      marginBottom: portrait ? 18 : 12,
    }}
  >
    {children}
  </div>
);

const FilmScene: React.FC<{
  portrait: boolean;
  image: string;
  eyebrow: string;
  title: React.ReactNode;
  source: string;
  caption?: string;
  captionsVisible: boolean;
  anchor?: string;
  accent?: string;
  titleWidth?: string;
}> = ({
  portrait,
  image,
  eyebrow,
  title,
  source,
  caption,
  captionsVisible,
  anchor = 'center',
  accent = TEAL,
  titleWidth = portrait ? '86%' : '68%',
}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const reveal = spring({frame, fps, config: {damping: 18, stiffness: 110}});
  const drift = interpolate(frame, [0, durationInFrames], [1.02, 1.075], clamp);
  return (
    <AbsoluteFill style={{backgroundColor: NAVY, overflow: 'hidden'}}>
      <Img
        src={asset(image)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: anchor,
          transform: `scale(${drift})`,
        }}
      />
      <AbsoluteFill
        style={{
          background: portrait
            ? 'linear-gradient(180deg, rgba(3,9,15,.06) 0%, rgba(3,9,15,.18) 35%, rgba(3,9,15,.92) 77%, #07111c 100%)'
            : 'linear-gradient(90deg, rgba(3,9,15,.93) 0%, rgba(3,9,15,.72) 42%, rgba(3,9,15,.10) 76%, rgba(3,9,15,.44) 100%)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: portrait ? 58 : 76,
          top: portrait ? 970 : 245,
          width: titleWidth,
          transform: `translateY(${(1 - reveal) * 36}px)`,
          opacity: reveal,
          zIndex: 10,
        }}
      >
        <Eyebrow portrait={portrait} color={accent}>{eyebrow}</Eyebrow>
        <div
          style={{
            color: INK,
            fontFamily: 'Arial, sans-serif',
            fontSize: portrait ? 74 : 68,
            lineHeight: .98,
            fontWeight: 900,
            letterSpacing: -2.4,
          }}
        >
          {title}
        </div>
        <div style={{marginTop: 24, width: portrait ? 150 : 180, height: 4, background: accent}} />
      </div>
      {captionsVisible && caption ? <Caption portrait={portrait}>{caption}</Caption> : null}
      <Source portrait={portrait}>{source}</Source>
    </AbsoluteFill>
  );
};

const MapToVessel: React.FC<{portrait: boolean; captionsVisible: boolean}> = ({portrait, captionsVisible}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const split = interpolate(frame, [24, 52], [portrait ? 0 : 46, portrait ? 50 : 54], clamp);
  const pulse = interpolate(frame, [0, durationInFrames * .58, durationInFrames], [0, 1, .2], clamp);
  return (
    <AbsoluteFill style={{backgroundColor: NAVY, overflow: 'hidden'}}>
      <Img
        src={asset(portrait ? 'eia-hormuz-map-portrait.png' : 'eia-hormuz-map-landscape.png')}
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: portrait
            ? 'translateX(-80px) scale(1.04)'
            : 'translateX(-220px) scale(.95)',
          transformOrigin: 'left top',
          clipPath: portrait ? undefined : 'inset(0 0 190px 0)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: portrait ? `${split}%` : 0,
          bottom: 0,
          left: portrait ? 0 : `${split}%`,
          right: 0,
          overflow: 'hidden',
          borderTop: portrait ? `5px solid ${TEAL}` : undefined,
          borderLeft: portrait ? undefined : `5px solid ${TEAL}`,
        }}
      >
        <Img
          src={asset('usns-oiler-strait-of-hormuz.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'center'}}
        />
        <AbsoluteFill style={{background: 'linear-gradient(180deg, transparent 15%, rgba(5,12,19,.88) 100%)'}} />
      </div>
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 0,
          height: portrait ? 182 : 238,
          background: NAVY,
          zIndex: 4,
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: portrait ? 54 : 72,
          right: portrait ? 54 : 72,
          top: portrait ? 98 : 68,
          display: 'flex',
          justifyContent: 'space-between',
          color: INK,
          fontFamily: 'Arial, sans-serif',
          fontWeight: 900,
          fontSize: portrait ? 38 : 34,
          letterSpacing: 1.4,
          zIndex: 8,
        }}
      >
        <span>STRAIT OF HORMUZ</span>
        <span style={{color: TEAL, opacity: pulse}}>TRAFFIC ↑</span>
      </div>
      <div
        style={{
          position: 'absolute',
          left: portrait ? 54 : 72,
          bottom: portrait ? 270 : 182,
          color: INK,
          fontFamily: 'Arial, sans-serif',
          fontSize: portrait ? 62 : 58,
          lineHeight: 1,
          fontWeight: 900,
          maxWidth: portrait ? 900 : 920,
        }}
      >
        MOVEMENT IS VISIBLE.
        <br />
        <span style={{color: COPPER}}>SUPPLY IS THE TEST.</span>
      </div>
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 0,
          height: portrait ? 118 : 70,
          background: 'rgba(5,12,19,.94)',
          zIndex: 20,
        }}
      />
      {captionsVisible ? (
        <Caption portrait={portrait}>EIA reported more traffic through Hormuz. But a moving ship is not yet restored supply.</Caption>
      ) : null}
      <Source portrait={portrait}>Map: U.S. EIA · Vessel: U.S. Navy, public domain · Editorial composition: Capital Chronicle</Source>
    </AbsoluteFill>
  );
};

const PhysicalChain: React.FC<{portrait: boolean; captionsVisible: boolean}> = ({portrait, captionsVisible}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const steps = [
    ['01', 'UNLOAD', 'doe-tanker-terminal-pipeline.jpg'],
    ['02', 'RESTORE', 'nara-refinery-portrait.jpg'],
    ['03', 'REBUILD', 'refinery-storage-tanks.jpg'],
  ];
  return (
    <AbsoluteFill style={{backgroundColor: NAVY, padding: portrait ? '92px 48px 150px' : '58px 66px 68px', display: 'flex', flexDirection: 'column'}}>
      <Eyebrow portrait={portrait}>THE PHYSICAL CHAIN</Eyebrow>
      <div style={{color: INK, fontFamily: 'Arial, sans-serif', fontSize: portrait ? 54 : 48, fontWeight: 900}}>
        TRAFFIC HAS TO BECOME BARRELS.
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: portrait ? '1fr' : 'repeat(3, 1fr)',
          gridTemplateRows: portrait ? 'repeat(3, minmax(0, 1fr))' : '1fr',
          gap: portrait ? 18 : 20,
          flex: 1,
          minHeight: 0,
          marginTop: portrait ? 38 : 34,
        }}
      >
        {steps.map(([number, label, image], index) => {
          const reveal = spring({frame: frame - index * 16, fps, config: {damping: 19, stiffness: 120}});
          return (
            <div key={label} style={{position: 'relative', overflow: 'hidden', minHeight: 0, opacity: reveal, transform: `translateY(${(1 - reveal) * 28}px)`}}>
              <Img src={asset(image)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
              <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(5,12,19,.05), rgba(5,12,19,.88))'}} />
              <div style={{position: 'absolute', left: 24, bottom: 24, fontFamily: 'Arial, sans-serif', color: INK}}>
                <div style={{fontSize: portrait ? 22 : 18, color: TEAL, fontWeight: 800}}>{number}</div>
                <div style={{fontSize: portrait ? 48 : 40, fontWeight: 900}}>{label}</div>
              </div>
            </div>
          );
        })}
      </div>
      {captionsVisible ? <Caption portrait={portrait}>Oil must unload, shut-in production must return, and inventories must rebuild.</Caption> : null}
      <Source portrait={portrait}>Archival U.S. government infrastructure imagery · Storage: Tony Webster, CC BY 4.0</Source>
    </AbsoluteFill>
  );
};

const DocumentScene: React.FC<{portrait: boolean; captionsVisible: boolean}> = ({portrait, captionsVisible}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const reveal = interpolate(frame, [12, 34], [0, 1], clamp);
  const documentScale = interpolate(frame, [0, durationInFrames], [1, 1.045], clamp);
  const documentShift = interpolate(frame, [0, durationInFrames], [0, portrait ? -18 : -10], clamp);
  return (
    <AbsoluteFill style={{backgroundColor: NAVY, overflow: 'hidden'}}>
      <Img
        src={asset(portrait ? 'eia-release-document-portrait.png' : 'eia-release-document-landscape.png')}
        style={{
          position: 'absolute',
          left: portrait ? 54 : 650,
          top: portrait ? 240 : 70,
          width: portrait ? 972 : 1160,
          height: portrait ? 1360 : 940,
          objectFit: 'contain',
          filter: 'drop-shadow(0 22px 40px rgba(0,0,0,.45))',
          transform: `translateY(${documentShift}px) scale(${documentScale})`,
        }}
      />
      <div style={{position: 'absolute', left: portrait ? 54 : 72, top: portrait ? 72 : 105, width: portrait ? 940 : 520}}>
        <Eyebrow portrait={portrait} color={COPPER}>SOURCE ON RECORD · JUL 7, 2026</Eyebrow>
        <div style={{fontFamily: 'Arial, sans-serif', color: INK, fontWeight: 900, fontSize: portrait ? 60 : 62, lineHeight: 1.02}}>
          FORECAST.
          <br />
          <span style={{color: TEAL}}>NOT A RESULT.</span>
        </div>
        <div style={{marginTop: 28, color: MUTED, fontFamily: 'Arial, sans-serif', fontSize: portrait ? 27 : 25, lineHeight: 1.35, opacity: reveal}}>
          EIA expects flows and prices to move toward pre-conflict conditions. The date and the forecast boundary stay visible.
        </div>
      </div>
      {captionsVisible ? <Caption portrait={portrait}>The source is EIA's July seventh release. Its forward path is a forecast, not an observed result.</Caption> : null}
      <Source portrait={portrait}>Source: U.S. Energy Information Administration, July 7, 2026</Source>
    </AbsoluteFill>
  );
};

const ForecastScene: React.FC<{portrait: boolean; captionsVisible: boolean}> = ({portrait, captionsVisible}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const progress = interpolate(frame, [18, durationInFrames - 28], [0, 1], clamp);
  const points = [
    {x: 0, y: 0, label: '$85', sub: 'JUNE · REFERENCE', color: INK},
    {x: .52, y: .58, label: '$74', sub: 'Q3 · FORECAST', color: TEAL},
    {x: 1, y: 1, label: '$65', sub: '2027 · FORECAST', color: COPPER},
  ];
  const w = portrait ? 820 : 1180;
  const h = portrait ? 820 : 560;
  const left = portrait ? 130 : 620;
  const top = portrait ? 540 : 250;
  return (
    <AbsoluteFill style={{backgroundColor: NAVY}}>
      <div style={{position: 'absolute', left: portrait ? 58 : 72, top: portrait ? 80 : 76}}>
        <Eyebrow portrait={portrait}>BRENT · REFERENCE VS. FORECAST</Eyebrow>
        <div style={{color: INK, fontFamily: 'Arial, sans-serif', fontSize: portrait ? 58 : 58, fontWeight: 900, lineHeight: 1}}>
          THE PATH IS DOWN.
          <br />
          <span style={{color: COPPER}}>THE OUTCOME IS OPEN.</span>
        </div>
      </div>
      <svg style={{position: 'absolute', left, top}} width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
        <line x1="35" y1="65" x2={35 + (w - 70) * progress} y2={65 + (h - 130) * progress} stroke={TEAL} strokeWidth="5" />
        {points.map((point, index) => {
          const x = 35 + (w - 70) * point.x;
          const y = 65 + (h - 130) * point.y;
          const visible = progress >= point.x - .03;
          return (
            <g key={point.label} opacity={visible ? 1 : 0}>
              <circle cx={x} cy={y} r="10" fill={point.color} />
              <text x={x} y={y - 30} fill={point.color} textAnchor={index === 0 ? 'start' : index === 2 ? 'end' : 'middle'} fontFamily="Arial" fontSize={portrait ? 54 : 48} fontWeight="900">{point.label}</text>
              <text x={x} y={y + 45} fill={MUTED} textAnchor={index === 0 ? 'start' : index === 2 ? 'end' : 'middle'} fontFamily="Arial" fontSize={portrait ? 22 : 20} fontWeight="700">{point.sub}</text>
            </g>
          );
        })}
      </svg>
      <div style={{position: 'absolute', left: portrait ? 58 : 72, bottom: portrait ? 250 : 120, color: portrait ? INK : MUTED, opacity: portrait ? .82 : 1, fontFamily: 'Arial, sans-serif', fontSize: portrait ? 30 : 23}}>
        Near pre-conflict levels by year-end · EIA forecast language
      </div>
      {captionsVisible ? <Caption portrait={portrait}>June Brent was eighty-five dollars. EIA forecasts seventy-four in Q3 and sixty-five in 2027.</Caption> : null}
      <Source portrait={portrait}>Data: U.S. EIA July 2026 STEO · Native chart: Capital Chronicle</Source>
    </AbsoluteFill>
  );
};

const TransmissionScene: React.FC<{portrait: boolean; captionsVisible: boolean}> = ({portrait, captionsVisible}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const drift = interpolate(frame, [0, durationInFrames], [1.02, 1.1], clamp);
  const nodes = portrait ? ['IMPORTERS', 'INFLATION', 'YIELDS'] : ['IMPORTERS · POSSIBLE SUPPORT', 'INFLATION · MAY EASE', 'LONG YIELDS · NO GUARANTEE'];
  return (
    <AbsoluteFill style={{backgroundColor: NAVY, overflow: 'hidden'}}>
      <Img src={asset('cc-energy-flow-illustration-v1.png')} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${drift})`}} />
      <AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(4,10,18,.9), rgba(4,10,18,.22), rgba(4,10,18,.62))'}} />
      <div style={{position: 'absolute', left: portrait ? 58 : 72, top: portrait ? 82 : 62}}>
        <Eyebrow portrait={portrait} color={COPPER}>ILLUSTRATIVE ANALYSIS · NOT EVIDENCE</Eyebrow>
        <div style={{color: INK, fontFamily: 'Arial, sans-serif', fontSize: portrait ? 64 : 62, fontWeight: 900}}>PRICE TRANSMISSION</div>
      </div>
      <div style={{position: 'absolute', left: portrait ? 58 : 72, right: portrait ? 58 : 72, top: portrait ? 540 : 430, display: 'grid', gridTemplateColumns: portrait ? '1fr' : 'repeat(3,1fr)', gap: 18}}>
        {nodes.map((node, index) => {
          const opacity = interpolate(frame, [20 + index * 12, 35 + index * 12], [0, 1], clamp);
          return <div key={node} style={{padding: portrait ? '26px 30px' : '24px', borderTop: `4px solid ${index === 2 ? COPPER : TEAL}`, background: 'rgba(5,12,19,.78)', color: INK, fontFamily: 'Arial, sans-serif', fontSize: portrait ? 34 : 28, fontWeight: 900, opacity}}>{node}</div>;
        })}
      </div>
      {captionsVisible ? <Caption portrait={portrait}>If the retreat lasts, importers may gain and inflation may ease. Lower long-term yields are not guaranteed.</Caption> : null}
      <Source portrait={portrait}>AI-generated illustrative transition by Codex ImageGen · No documentary or factual authority</Source>
    </AbsoluteFill>
  );
};

const ConsequenceScene: React.FC<{portrait: boolean; captionsVisible: boolean}> = ({portrait, captionsVisible}) => {
  const frame = useCurrentFrame();
  const blocks = [
    ['GASOLINE', '$3.80 → $3.40', TEAL],
    ['PRODUCER REVENUE', 'POSSIBLE PRESSURE', COPPER],
    ['FED', 'NO AUTOMATIC MOVE', INK],
  ];
  return (
    <AbsoluteFill style={{backgroundColor: NAVY, overflow: 'hidden'}}>
      <Img src={asset('refinery-storage-tanks.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      <AbsoluteFill style={{background: portrait ? 'rgba(4,10,18,.68)' : 'linear-gradient(90deg, rgba(4,10,18,.9), rgba(4,10,18,.34))'}} />
      <div style={{position: 'absolute', left: portrait ? 58 : 72, top: portrait ? 80 : 70}}>
        <Eyebrow portrait={portrait}>BEYOND THE BARREL</Eyebrow>
        <div style={{fontFamily: 'Arial, sans-serif', color: INK, fontSize: portrait ? 58 : 56, fontWeight: 900}}>CONDITIONS, NOT CERTAINTIES.</div>
      </div>
      <div style={{position: 'absolute', left: portrait ? 58 : 72, right: portrait ? 58 : 760, top: portrait ? 440 : 300, display: 'grid', gap: 16}}>
        {blocks.map(([label, value, color], index) => {
          const reveal = interpolate(frame, [12 + index * 15, 30 + index * 15], [0, 1], clamp);
          return (
            <div key={label} style={{padding: portrait ? '24px 28px' : '20px 24px', background: 'rgba(5,12,19,.85)', borderLeft: `6px solid ${color}`, opacity: reveal}}>
              <div style={{color: MUTED, fontFamily: 'Arial, sans-serif', fontSize: portrait ? 21 : 18, fontWeight: 800, letterSpacing: 2}}>{label}</div>
              <div style={{color, fontFamily: 'Arial, sans-serif', fontSize: portrait ? 42 : 38, fontWeight: 900, marginTop: 5}}>{value}</div>
            </div>
          );
        })}
      </div>
      {captionsVisible ? <Caption portrait={portrait}>EIA forecasts gasoline at three-eighty in Q3 and three-forty in Q4. Gasoline alone does not dictate the Fed.</Caption> : null}
      <Source portrait={portrait}>Forecast: U.S. EIA, July 7, 2026 · Image: Tony Webster, CC BY 4.0</Source>
    </AbsoluteFill>
  );
};

const TestScene: React.FC<{portrait: boolean; captionsVisible: boolean}> = ({portrait, captionsVisible}) => {
  const frame = useCurrentFrame();
  const confirm = ['HORMUZ TRAFFIC NORMALIZES', 'PRODUCTION RETURNS', 'INVENTORIES BUILD', 'BRENT TRACKS THE PATH'];
  const challenge = ['RENEWED DISRUPTION', 'SLOWER RESTARTS', 'PERSISTENT DRAWS', 'PRICES ABOVE PATH'];
  const list = (title: string, rows: string[], color: string, offset: number) => (
    <div style={{padding: portrait ? '28px 28px' : '30px 34px', background: 'rgba(5,12,19,.84)', borderTop: `5px solid ${color}`}}>
      <div style={{color, fontFamily: 'Arial, sans-serif', fontSize: portrait ? 42 : 38, fontWeight: 900, marginBottom: 20}}>{title}</div>
      {rows.map((row, index) => <div key={row} style={{display: 'flex', gap: 14, margin: '13px 0', opacity: interpolate(frame, [offset + index * 8, offset + index * 8 + 12], [0,1], clamp), color: INK, fontFamily: 'Arial, sans-serif', fontSize: portrait ? 25 : 23, fontWeight: 800}}><span style={{color}}>0{index + 1}</span><span>{row}</span></div>)}
    </div>
  );
  return (
    <AbsoluteFill style={{backgroundColor: NAVY, overflow: 'hidden'}}>
      <Img src={asset('refinery-storage-tanks.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      <AbsoluteFill style={{background: 'rgba(4,10,18,.66)'}} />
      <div style={{position: 'absolute', left: portrait ? 58 : 72, top: portrait ? 76 : 58}}>
        <Eyebrow portrait={portrait}>THE REBALANCE TEST</Eyebrow>
        <div style={{color: INK, fontFamily: 'Arial, sans-serif', fontSize: portrait ? 58 : 56, fontWeight: 900}}>WHAT WOULD PROVE IT?</div>
      </div>
      <div style={{position: 'absolute', left: portrait ? 48 : 72, right: portrait ? 48 : 72, top: portrait ? 340 : 230, display: 'grid', gridTemplateColumns: portrait ? '1fr' : '1fr 1fr', gap: 18}}>
        {list('CONFIRM IF', confirm, TEAL, 10)}
        {list('CHALLENGE IF', challenge, COPPER, portrait ? 44 : 18)}
      </div>
      {captionsVisible ? <Caption portrait={portrait}>Watch traffic, production, inventories and Brent together. Disruption, slow restarts, draws or above-path prices would challenge the forecast.</Caption> : null}
      <Source portrait={portrait}>Conditions: governed Capital Chronicle analysis · Forecast boundary: U.S. EIA</Source>
    </AbsoluteFill>
  );
};

const CheckpointScene: React.FC<{portrait: boolean; captionsVisible: boolean}> = ({portrait, captionsVisible}) => {
  const frame = useCurrentFrame();
  const line = interpolate(frame, [12, 52], [0, 1], clamp);
  return (
    <AbsoluteFill style={{backgroundColor: NAVY}}>
      <div style={{position: 'absolute', left: portrait ? 58 : 72, top: portrait ? 90 : 80}}>
        <Eyebrow portrait={portrait} color={COPPER}>OBSERVATION ≠ FORECAST</Eyebrow>
        <div style={{color: INK, fontFamily: 'Arial, sans-serif', fontSize: portrait ? 72 : 68, fontWeight: 900}}>$69.60 <span style={{fontSize: portrait ? 28 : 24, color: MUTED}}>WTI · JUL 6</span></div>
      </div>
      <div style={{position: 'absolute', left: portrait ? 58 : 72, right: portrait ? 58 : 72, top: portrait ? 560 : 400}}>
        <div style={{height: 4, width: `${line * 100}%`, background: `linear-gradient(90deg, ${TEAL}, ${COPPER})`}} />
        <div style={{display: 'flex', justifyContent: 'space-between', marginTop: 26, color: INK, fontFamily: 'Arial, sans-serif', fontWeight: 900, fontSize: portrait ? 34 : 32}}>
          <span>JUL 15</span><span>AUG 11</span>
        </div>
        <div style={{marginTop: portrait ? 100 : 60, color: MUTED, fontFamily: 'Arial, sans-serif', fontSize: portrait ? 28 : 27, lineHeight: 1.4, maxWidth: 1150}}>
          WTI is a separate observed benchmark. It does not prove the Brent forecast. Test the conditions at each checkpoint.
        </div>
      </div>
      <div style={{position: 'absolute', left: portrait ? 58 : 72, bottom: portrait ? 250 : 130, color: INK, fontFamily: 'Arial, sans-serif', fontSize: portrait ? 48 : 44, fontWeight: 900}}>
        CAPITAL <span style={{color: TEAL}}>CHRONICLE</span>
      </div>
      {captionsVisible ? <Caption portrait={portrait}>WTI was sixty-nine sixty on July sixth. Check July fifteenth and August eleventh, but test conditions—not a promised outcome.</Caption> : null}
      <Source portrait={portrait}>WTI observation: FRED DCOILWTICO · Checkpoints and Brent forecast: U.S. EIA</Source>
    </AbsoluteFill>
  );
};

const shortScenes = [90, 180, 210, 210, 240, 160, 215, 210, 201];
const midScenes = [210, 270, 360, 270, 450, 240, 480, 630, 510, 240];

export const CodexBuilderShort: React.FC<VariantProps> = ({captionsVisible}) => {
  const scenes: React.ReactNode[] = [
    <FilmScene key="hook" portrait image="nasa-persian-gulf-iss069-e-92132.jpg" eyebrow="OIL · GEOGRAPHY · NOW" title={<>ONE CHOKEPOINT.<br/><span style={{color: TEAL}}>FOUR TESTS.</span></>} source="NASA ISS Crew Earth Observations · Geographic context" caption="The oil story starts at one narrow exit from the Persian Gulf." captionsVisible={captionsVisible} anchor="center" />,
    <MapToVessel key="map" portrait captionsVisible={captionsVisible} />,
    <PhysicalChain key="chain" portrait captionsVisible={captionsVisible} />,
    <DocumentScene key="doc" portrait captionsVisible={captionsVisible} />,
    <ForecastScene key="forecast" portrait captionsVisible={captionsVisible} />,
    <TransmissionScene key="transmission" portrait captionsVisible={captionsVisible} />,
    <ConsequenceScene key="consequence" portrait captionsVisible={captionsVisible} />,
    <TestScene key="test" portrait captionsVisible={captionsVisible} />,
    <CheckpointScene key="checkpoints" portrait captionsVisible={captionsVisible} />,
  ];
  let at = 0;
  return <AbsoluteFill style={{backgroundColor: NAVY}}>{scenes.map((scene, index) => {const from = at; at += shortScenes[index]; return <Sequence key={index} from={from} durationInFrames={shortScenes[index]}>{scene}</Sequence>;})}</AbsoluteFill>;
};

export const CodexBuilderMidform: React.FC<VariantProps> = ({captionsVisible}) => {
  const scenes: React.ReactNode[] = [
    <FilmScene key="orbit" portrait={false} image="nasa-persian-gulf-iss069-e-92132.jpg" eyebrow="ORBITAL GEOGRAPHY" title={<>THE PERSIAN GULF<br/><span style={{color: TEAL}}>HAS ONE NARROW EXIT.</span></>} source="NASA astronaut photograph ISS069-E-92132" caption="The supply question begins with geography: the Persian Gulf has one narrow exit." captionsVisible={captionsVisible} />,
    <MapToVessel key="map" portrait={false} captionsVisible={captionsVisible} />,
    <PhysicalChain key="chain" portrait={false} captionsVisible={captionsVisible} />,
    <FilmScene key="transit" portrait={false} image="commercial-tanker-oil-platform-persian-gulf.jpg" eyebrow="TRANSIT LIMIT" title={<>A SHIP PAST HORMUZ<br/><span style={{color: COPPER}}>IS NOT RESTORED SUPPLY.</span></>} source="U.S. Navy archival context · Mechanism: Capital Chronicle" caption="Transit establishes movement. Supply still depends on unloading, production and storage." captionsVisible={captionsVisible} anchor="center" />,
    <DocumentScene key="doc" portrait={false} captionsVisible={captionsVisible} />,
    <ForecastScene key="forecast" portrait={false} captionsVisible={captionsVisible} />,
    <TransmissionScene key="transmission" portrait={false} captionsVisible={captionsVisible} />,
    <ConsequenceScene key="consequence" portrait={false} captionsVisible={captionsVisible} />,
    <TestScene key="test" portrait={false} captionsVisible={captionsVisible} />,
    <CheckpointScene key="checkpoints" portrait={false} captionsVisible={captionsVisible} />,
  ];
  let at = 0;
  return <AbsoluteFill style={{backgroundColor: NAVY}}>{scenes.map((scene, index) => {const from = at; at += midScenes[index]; return <Sequence key={index} from={from} durationInFrames={midScenes[index]}>{scene}</Sequence>;})}</AbsoluteFill>;
};

export const codexBuilderShortFrames = shortScenes.reduce((sum, value) => sum + value, 0);
export const codexBuilderMidformFrames = midScenes.reduce((sum, value) => sum + value, 0);
