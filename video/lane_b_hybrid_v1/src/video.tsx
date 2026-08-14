import React from 'react';
import {Audio} from '@remotion/media';
import {
  AbsoluteFill,
  Easing,
  Img,
  Series,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export type Primitive =
  | 'MAP_TO_VESSEL'
  | 'PHYSICAL_CHAIN'
  | 'DOCUMENT_EVIDENCE'
  | 'NATIVE_FORECAST_CHART'
  | 'TRANSMISSION'
  | 'CONSEQUENCE'
  | 'CONFIRM_CHALLENGE'
  | 'CHECKPOINT_TIMELINE';

export type Scene = {
  scene_id: string;
  duration_seconds: number;
  primitive: Primitive;
  asset_id: string;
  title: string;
  body: string;
  source: string;
  narration: string;
  callouts?: string[];
  status_label?: string;
};

export type HybridVideoProps = {
  owner_label: string;
  run_id: string;
  audio_file: string;
  scenes: Scene[];
};

const NAVY = '#07111c';
const SURFACE = '#102230';
const INK = '#f4f0e7';
const MUTED = '#a9bbc5';
const TEAL = '#47d6bd';
const COPPER = '#d79a58';
const RED = '#ee776d';

const assetFiles: Record<string, string> = {
  'nasa-persian-gulf': 'nasa-persian-gulf-iss069-e-92132.jpg',
  'usns-oiler-hormuz': 'usns-oiler-strait-of-hormuz.jpg',
  'commercial-tanker-platform': 'commercial-tanker-oil-platform-persian-gulf.jpg',
  'refinery-storage-tanks': 'refinery-storage-tanks.jpg',
  'nara-refinery-portrait': 'nara-refinery-portrait.jpg',
  'doe-tanker-terminal-pipeline': 'doe-tanker-terminal-pipeline.jpg',
  'crude-oil-supertanker': 'crude-oil-supertanker.jpg',
  'eia-hormuz-map-portrait': 'eia-hormuz-map-portrait.png',
  'eia-hormuz-map-landscape': 'eia-hormuz-map-landscape.png',
  'eia-brent-forecast-portrait': 'eia-brent-forecast-portrait.png',
  'eia-brent-forecast-landscape': 'eia-brent-forecast-landscape.png',
  'eia-release-document-portrait': 'eia-release-document-portrait.png',
  'eia-release-document-landscape': 'eia-release-document-landscape.png',
};

const useEntrance = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return interpolate(frame, [0, 0.42 * fps], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
};

const Background: React.FC<{assetId: string; darken?: number}> = ({assetId, darken = 0.46}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const filename = assetFiles[assetId];
  return (
    <AbsoluteFill>
      {filename ? (
        <Img
          src={staticFile(`assets/${filename}`)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            scale: interpolate(frame, [0, durationInFrames], [1.015, 1.075], {
              extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.linear,
            }),
          }}
        />
      ) : null}
      <AbsoluteFill style={{background: `linear-gradient(180deg, rgba(7,17,28,${darken}) 0%, rgba(7,17,28,.9) 78%, ${NAVY} 100%)`}} />
    </AbsoluteFill>
  );
};

const Chrome: React.FC<{scene: Scene; children: React.ReactNode; accent?: string}> = ({scene, children, accent = TEAL}) => {
  const enter = useEntrance();
  return (
    <AbsoluteFill style={{backgroundColor: NAVY, color: INK, fontFamily: 'Arial, Helvetica, sans-serif'}}>
      {children}
      <div style={{position: 'absolute', left: 62, top: 70, color: accent, fontSize: 25, fontWeight: 800, letterSpacing: 4}}>
        CAPITAL CHRONICLE · {scene.primitive.replaceAll('_', ' ')}
      </div>
      <div style={{position: 'absolute', left: 62, right: 62, bottom: 58, height: 66, overflow: 'hidden', borderTop: '2px solid rgba(255,255,255,.18)', paddingTop: 15, color: MUTED, fontSize: 25, lineHeight: 1.18, overflowWrap: 'anywhere'}}>
        {scene.source}
      </div>
      <div style={{position: 'absolute', left: 62, top: 112, width: 7, height: 112, backgroundColor: accent, scale: `1 ${enter}`, transformOrigin: 'top'}} />
    </AbsoluteFill>
  );
};

const Headline: React.FC<{scene: Scene; accent?: string; top?: number}> = ({scene, accent = TEAL, top = 245}) => {
  const enter = useEntrance();
  return (
    <div style={{position: 'absolute', left: 70, right: 70, top, opacity: enter, translate: `0 ${36 * (1 - enter)}px`}}>
      <div style={{fontSize: 84, lineHeight: .96, fontWeight: 900, letterSpacing: -3, textTransform: 'uppercase'}}>{scene.title}</div>
      <div style={{marginTop: 28, maxWidth: 880, fontSize: 37, lineHeight: 1.2, color: INK}}>{scene.body}</div>
      <div style={{marginTop: 24, width: 150, height: 6, backgroundColor: accent}} />
    </div>
  );
};

const MapToVessel: React.FC<{scene: Scene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const split = interpolate(frame, [1.1 * fps, 2.1 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(.16, 1, .3, 1)});
  return (
    <Chrome scene={scene}>
      <Img src={staticFile('assets/eia-hormuz-map-portrait.png')} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'}} />
      <div style={{position: 'absolute', left: 86, right: 86, top: 250, height: 600, overflow: 'hidden', border: `3px solid ${TEAL}`}}>
        <Img src={staticFile('assets/usns-oiler-strait-of-hormuz.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', translate: `${(1 - split) * 1050}px 0`}} />
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 855, bottom: 0, background: 'linear-gradient(180deg, rgba(7,17,28,.08), rgba(7,17,28,.96) 22%, #07111c 100%)'}} />
      <Headline scene={scene} top={950} />
    </Chrome>
  );
};

const PhysicalChain: React.FC<{scene: Scene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const labels = scene.callouts?.slice(0, 4) ?? ['TRANSIT', 'UNLOAD', 'RESTORE', 'REBUILD'];
  return (
    <Chrome scene={scene} accent={COPPER}>
      <Background assetId={scene.asset_id} darken={.62} />
      <Headline scene={scene} accent={COPPER} top={245} />
      <div style={{position: 'absolute', left: 70, right: 70, top: 840, display: 'grid', gap: 18}}>
        {labels.map((label, index) => {
          const reveal = interpolate(frame, [(1 + index * .42) * fps, (1.34 + index * .42) * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(.16, 1, .3, 1)});
          return <div key={label} style={{height: 122, display: 'flex', alignItems: 'center', gap: 28, padding: '0 34px', backgroundColor: 'rgba(7,17,28,.82)', outline: '2px solid rgba(255,255,255,.18)', opacity: reveal, translate: `${80 * (1 - reveal)}px 0`}}><b style={{fontSize: 54, color: COPPER}}>{index + 1}</b><span style={{fontSize: 46, fontWeight: 850, letterSpacing: 2}}>{label}</span></div>;
        })}
      </div>
    </Chrome>
  );
};

const DocumentEvidence: React.FC<{scene: Scene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  return (
    <Chrome scene={scene} accent={COPPER}>
      <div style={{position: 'absolute', left: 55, right: 55, top: 175, height: 1020, backgroundColor: '#e9e5dc', overflow: 'hidden', boxShadow: '0 24px 70px #0008'}}>
        <Img src={staticFile('assets/eia-release-document-portrait.png')} style={{width: '100%', height: '100%', objectFit: 'contain', scale: interpolate(frame, [0, durationInFrames], [1, 1.045], {extrapolateRight: 'clamp'})}} />
      </div>
      <div style={{position: 'absolute', left: 70, right: 70, top: 1240, backgroundColor: 'rgba(7,17,28,.95)', padding: '32px 38px', outline: `3px solid ${COPPER}`}}>
        <div style={{fontSize: 67, lineHeight: .98, fontWeight: 900, color: COPPER}}>{scene.status_label ?? 'FORECAST. NOT A RESULT.'}</div>
        <div style={{fontSize: 33, lineHeight: 1.25, marginTop: 22}}>{scene.body}</div>
      </div>
    </Chrome>
  );
};

const ForecastChart: React.FC<{scene: Scene}> = ({scene}) => {
  const enter = useEntrance();
  return (
    <Chrome scene={scene}>
      <Background assetId="refinery-storage-tanks" darken={.7} />
      <Headline scene={scene} top={225} />
      <div style={{position: 'absolute', left: 48, right: 48, top: 730, height: 850, backgroundColor: '#f4f0e7', padding: 26, opacity: enter, scale: .94 + .06 * enter}}>
        <Img src={staticFile('assets/eia-brent-forecast-portrait.png')} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
      </div>
    </Chrome>
  );
};

const Transmission: React.FC<{scene: Scene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const labels = scene.callouts?.slice(0, 4) ?? ['CRUDE', 'IMPORT COST', 'GASOLINE', 'INFLATION'];
  return (
    <Chrome scene={scene} accent={COPPER}>
      <Background assetId={scene.asset_id} darken={.72} />
      <Headline scene={scene} accent={COPPER} top={225} />
      <div style={{position: 'absolute', left: 65, right: 65, top: 900, display: 'flex', flexDirection: 'column', gap: 28}}>
        {labels.map((label, index) => <React.Fragment key={label}><div style={{padding: '30px 34px', backgroundColor: index % 2 ? SURFACE : '#163947', outline: `2px solid ${index % 2 ? COPPER : TEAL}`, fontSize: 45, fontWeight: 850, opacity: interpolate(frame, [(1 + index * .34) * fps, (1.3 + index * .34) * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}}>{label}</div>{index < labels.length - 1 ? <div style={{height: 28, width: 5, alignSelf: 'center', backgroundColor: COPPER}} /> : null}</React.Fragment>)}
      </div>
    </Chrome>
  );
};

const Consequence: React.FC<{scene: Scene}> = ({scene}) => (
  <Chrome scene={scene} accent={COPPER}>
    <Background assetId={scene.asset_id} darken={.72} />
    <Headline scene={scene} accent={COPPER} top={225} />
    <div style={{position: 'absolute', left: 65, right: 65, top: 940, display: 'grid', gap: 24}}>
      {(scene.callouts ?? ['IMPORTERS: LOWER COST', 'PRODUCERS: LOWER REVENUE', 'FED: STILL CONDITIONAL']).slice(0, 3).map((item, index) => <div key={item} style={{padding: 34, backgroundColor: 'rgba(7,17,28,.9)', borderLeft: `9px solid ${index === 2 ? COPPER : TEAL}`, fontSize: 42, lineHeight: 1.15, fontWeight: 800}}>{item}</div>)}
    </div>
  </Chrome>
);

const ConfirmChallenge: React.FC<{scene: Scene}> = ({scene}) => {
  const items = scene.callouts ?? ['TRAFFIC NORMALIZES', 'PRODUCTION RETURNS', 'INVENTORIES BUILD', 'DISRUPTION RETURNS', 'DRAWS PERSIST', 'PRICE HOLDS ABOVE PATH'];
  return (
    <Chrome scene={scene}>
      <Background assetId={scene.asset_id} darken={.77} />
      <Headline scene={scene} top={220} />
      <div style={{position: 'absolute', left: 55, right: 55, top: 850, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18}}>
        {[{label: 'CONFIRM IF', color: TEAL, values: items.slice(0, 3)}, {label: 'CHALLENGE IF', color: RED, values: items.slice(3, 6)}].map(column => <div key={column.label} style={{backgroundColor: 'rgba(7,17,28,.9)', padding: 25, outline: `3px solid ${column.color}`}}><div style={{fontSize: 39, color: column.color, fontWeight: 900, marginBottom: 26}}>{column.label}</div>{column.values.map(value => <div key={value} style={{fontSize: 29, lineHeight: 1.18, padding: '20px 0', borderTop: '1px solid #ffffff2b', fontWeight: 750}}>{value}</div>)}</div>)}
      </div>
    </Chrome>
  );
};

const Checkpoint: React.FC<{scene: Scene}> = ({scene}) => (
  <Chrome scene={scene} accent={COPPER}>
    <Background assetId={scene.asset_id} darken={.82} />
    <Headline scene={scene} accent={COPPER} top={250} />
    <div style={{position: 'absolute', left: 100, top: 890, bottom: 230, width: 8, backgroundColor: COPPER}} />
    <div style={{position: 'absolute', left: 70, right: 70, top: 880, display: 'grid', gap: 70}}>
      {(scene.callouts ?? ['HORMUZ TRAFFIC', 'PRODUCTION RESTARTS', 'INVENTORY DATA', 'NEXT EIA PATH']).slice(0, 4).map((item, index) => <div key={item} style={{display: 'flex', alignItems: 'center', gap: 38}}><div style={{width: 68, height: 68, borderRadius: 40, backgroundColor: COPPER, color: NAVY, display: 'grid', placeItems: 'center', fontWeight: 900, fontSize: 30}}>{index + 1}</div><div style={{fontSize: 39, fontWeight: 850}}>{item}</div></div>)}
    </div>
  </Chrome>
);

const SceneRenderer: React.FC<{scene: Scene}> = ({scene}) => {
  switch (scene.primitive) {
    case 'MAP_TO_VESSEL': return <MapToVessel scene={scene} />;
    case 'PHYSICAL_CHAIN': return <PhysicalChain scene={scene} />;
    case 'DOCUMENT_EVIDENCE': return <DocumentEvidence scene={scene} />;
    case 'NATIVE_FORECAST_CHART': return <ForecastChart scene={scene} />;
    case 'TRANSMISSION': return <Transmission scene={scene} />;
    case 'CONSEQUENCE': return <Consequence scene={scene} />;
    case 'CONFIRM_CHALLENGE': return <ConfirmChallenge scene={scene} />;
    case 'CHECKPOINT_TIMELINE': return <Checkpoint scene={scene} />;
  }
};

export const HybridShort: React.FC<HybridVideoProps> = ({scenes, audio_file}) => {
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{backgroundColor: NAVY}}>
      {audio_file ? <Audio src={staticFile(`audio/${audio_file}`)} volume={0.92} /> : null}
      <Series>
        {scenes.map(scene => (
          <Series.Sequence key={scene.scene_id} durationInFrames={Math.round(scene.duration_seconds * fps)} premountFor={fps}>
            <SceneRenderer scene={scene} />
          </Series.Sequence>
        ))}
      </Series>
    </AbsoluteFill>
  );
};
