import React from 'react';
import {
  AbsoluteFill,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {VariantProps} from '../types';

const TOTAL_FRAMES = 630;
const ORBIT_FRAMES = 165;
const MAP_FRAMES = 195;
const VESSEL_FRAMES = 270;

const TITLE_FONT = 'Bahnschrift Condensed, Franklin Gothic Medium, sans-serif';
const BODY_FONT = 'Trebuchet MS, Gill Sans, sans-serif';
const INK = '#071821';
const IVORY = '#f3f1e9';
const MUTED = '#c9d2d5';
const TEAL = '#147f74';
const AMBER = '#e6b85c';
const CLAMP = {
  extrapolateLeft: 'clamp',
  extrapolateRight: 'clamp',
} as const;

const fullImage: React.CSSProperties = {
  position: 'absolute',
  inset: 0,
  width: '100%',
  height: '100%',
};

const clamp01 = (value: number): number => Math.max(0, Math.min(1, value));

const smoothstep = (value: number): number => {
  const x = clamp01(value);
  return x * x * (3 - 2 * x);
};

const Caption: React.FC<{visible?: boolean; text: string}> = ({visible, text}) => {
  if (!visible) {
    return null;
  }

  return (
    <div
      style={{
        position: 'absolute',
        left: 150,
        right: 150,
        bottom: 122,
        zIndex: 30,
        textAlign: 'center',
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          display: 'inline-block',
          maxWidth: 1510,
          padding: '10px 18px 11px',
          borderRadius: 5,
          backgroundColor: 'rgba(3, 12, 17, 0.88)',
          color: '#ffffff',
          fontFamily: BODY_FONT,
          fontSize: 29,
          fontWeight: 700,
          lineHeight: 1.25,
          boxShadow: '0 2px 14px rgba(0, 0, 0, 0.32)',
        }}
      >
        {text}
      </div>
    </div>
  );
};

const SourceFooter: React.FC<{text: string}> = ({text}) => {
  return (
    <>
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 0,
          height: 102,
          zIndex: 14,
          background: 'linear-gradient(180deg, rgba(4, 15, 21, 0), rgba(4, 15, 21, 0.88) 56%, rgba(4, 15, 21, 0.96))',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 86,
          right: 86,
          bottom: 27,
          zIndex: 15,
          color: MUTED,
          fontFamily: BODY_FONT,
          fontSize: 22,
          fontWeight: 500,
          lineHeight: 1.25,
          letterSpacing: 0.15,
          textShadow: '0 2px 8px rgba(0, 0, 0, 0.9)',
          pointerEvents: 'none',
        }}
      >
        {text}
      </div>
    </>
  );
};

const PersianGulfOrbit: React.FC<{captionsVisible?: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const driftPhase = interpolate(
    frame,
    [0, 30, 150, ORBIT_FRAMES - 1],
    [0, 0.08, 1, 1],
    CLAMP,
  );
  const driftX = interpolate(driftPhase, [0, 1], [32, -40], CLAMP);
  const labelReveal = smoothstep((frame - 10) / 18);
  const caption =
    frame < 72
      ? 'The oil supply question begins at the Persian Gulf,'
      : 'where the route east narrows.';

  return (
    <AbsoluteFill
      data-beat-id={'S1_MID_01_PERSIAN_GULF_ORBIT'}
      style={{backgroundColor: INK, overflow: 'hidden'}}
    >
      <Img
        alt={'Persian Gulf and Strait of Hormuz region viewed from orbit'}
        src={staticFile('assets/nasa-persian-gulf-iss069-e-92132.jpg')}
        style={{
          ...fullImage,
          objectFit: 'cover',
          transform: `translate3d(${driftX}px, 0, 0) scale(1.06)`,
          transformOrigin: '50% 50%',
        }}
      />

      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(180deg, rgba(2, 8, 13, 0.06) 18%, rgba(3, 13, 19, 0.08) 42%, rgba(3, 13, 19, 0.77) 100%)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          left: 92,
          top: 650,
          zIndex: 10,
          display: 'flex',
          alignItems: 'stretch',
          gap: 24,
          opacity: labelReveal,
          transform: `translate3d(0, ${interpolate(labelReveal, [0, 1], [16, 0], CLAMP)}px, 0)`,
        }}
      >
        <div style={{width: 5, backgroundColor: AMBER}} />
        <div>
          <div
            style={{
              color: '#d8e1e3',
              fontFamily: BODY_FONT,
              fontSize: 22,
              fontWeight: 700,
              letterSpacing: 5.2,
              lineHeight: 1,
              marginBottom: 17,
            }}
          >
            ORBITAL GEOGRAPHY
          </div>
          <div
            style={{
              color: IVORY,
              fontFamily: TITLE_FONT,
              fontSize: 88,
              fontWeight: 700,
              letterSpacing: 1.5,
              lineHeight: 0.94,
              textShadow: '0 4px 22px rgba(0, 0, 0, 0.48)',
            }}
          >
            PERSIAN GULF
          </div>
        </div>
      </div>

      <Caption visible={captionsVisible} text={caption} />
      <SourceFooter text={'NASA astronaut photograph ISS069-E-92132 | ISS Crew Earth Observations Facility / JSC'} />
    </AbsoluteFill>
  );
};

const StraitMap: React.FC<{captionsVisible?: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const emphasis = smoothstep(frame / 9);
  const tickFrame = Math.round(MAP_FRAMES * 0.38);
  const tickPulse = clamp01(1 - Math.abs(frame - tickFrame) / 10);
  const caption =
    frame < 92
      ? 'That exit is the Strait of Hormuz,'
      : 'linking the Persian Gulf with the Gulf of Oman.';

  return (
    <AbsoluteFill
      data-beat-id={'S1_MID_02_LABEL_THE_STRAIT'}
      style={{backgroundColor: '#e7e5df', overflow: 'hidden'}}
    >
      <Img
        alt={'Labeled Strait of Hormuz between the Persian Gulf and Gulf of Oman'}
        src={staticFile('assets/eia-hormuz-map-landscape.png')}
        style={{
          ...fullImage,
          objectFit: 'contain',
          filter: 'contrast(1.03) saturate(0.96)',
        }}
      />

      <Img
        alt={''}
        src={staticFile('assets/eia-hormuz-map-landscape.png')}
        style={{
          ...fullImage,
          objectFit: 'contain',
          clipPath: 'inset(7% 3% 67% 74%)',
          filter: 'contrast(1.3) brightness(1.07) saturate(1.08)',
          opacity: emphasis * 0.74,
        }}
      />

      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(90deg, rgba(6, 20, 27, 0.08), rgba(6, 20, 27, 0) 37%, rgba(6, 20, 27, 0) 78%, rgba(6, 20, 27, 0.06))',
          pointerEvents: 'none',
        }}
      />

      <div
        style={{
          position: 'absolute',
          top: 68,
          left: 72,
          width: 620,
          zIndex: 12,
          padding: '22px 30px 24px 31px',
          borderLeft: `7px solid ${AMBER}`,
          backgroundColor: 'rgba(246, 243, 234, 0.93)',
          boxShadow: '0 10px 30px rgba(5, 20, 27, 0.18)',
          opacity: emphasis,
        }}
      >
        <div
          style={{
            color: TEAL,
            fontFamily: BODY_FONT,
            fontSize: 24,
            fontWeight: 800,
            letterSpacing: 4.8,
            lineHeight: 1,
            marginBottom: 14,
          }}
        >
          THE CHOKEPOINT
        </div>
        <div
          style={{
            color: INK,
            fontFamily: TITLE_FONT,
            fontSize: 57,
            fontWeight: 700,
            letterSpacing: 0.5,
            lineHeight: 0.98,
          }}
        >
          STRAIT OF HORMUZ
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          top: 96,
          right: 68,
          width: 390,
          height: 238,
          zIndex: 11,
          border: `3px solid rgba(230, 184, 92, ${0.38 + emphasis * 0.5})`,
          boxShadow: `0 0 ${20 + tickPulse * 16}px rgba(230, 184, 92, ${0.12 + tickPulse * 0.22})`,
          opacity: emphasis,
          pointerEvents: 'none',
        }}
      />

      <Caption visible={captionsVisible} text={caption} />
      <SourceFooter text={'Source map: U.S. Energy Information Administration | Format-native render: Capital Chronicle'} />
    </AbsoluteFill>
  );
};

const TrafficToSupply: React.FC<{captionsVisible?: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const introOpacity = smoothstep(frame / 13);
  const questionReveal = smoothstep((frame - 118) / 19);
  const push = smoothstep((frame - 122) / (VESSEL_FRAMES - 1 - 122));
  const claimTop = interpolate(questionReveal, [0, 1], [594, 554], CLAMP);
  const claimSize = interpolate(questionReveal, [0, 1], [67, 43], CLAMP);
  const claimOpacity = interpolate(questionReveal, [0, 1], [1, 0.82], CLAMP);
  const caption =
    frame < 122
      ? 'EIA reported increased Hormuz traffic following the June 18 U.S.-Iran memorandum.'
      : 'Now comes the physical test: does that movement become restored supply?';

  return (
    <AbsoluteFill
      data-beat-id={'S1_MID_03_TRAFFIC_TO_SUPPLY_REHOOK'}
      style={{backgroundColor: INK, overflow: 'hidden'}}
    >
      <Img
        alt={'Fleet replenishment oiler transiting the Strait of Hormuz'}
        src={staticFile('assets/usns-oiler-strait-of-hormuz.jpg')}
        style={{
          ...fullImage,
          objectFit: 'cover',
          transform: `translate3d(${-16 * push}px, ${8 * push}px, 0) scale(${1 + 0.065 * push})`,
          transformOrigin: '53% 48%',
        }}
      />

      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(180deg, rgba(2, 11, 16, 0.02) 20%, rgba(2, 11, 16, 0.13) 39%, rgba(2, 11, 16, 0.77) 61%, rgba(2, 11, 16, 0.94) 100%)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          left: 96,
          top: 477,
          zIndex: 12,
          padding: '15px 23px 16px',
          borderLeft: `6px solid ${AMBER}`,
          backgroundColor: 'rgba(20, 127, 116, 0.94)',
          color: '#ffffff',
          fontFamily: BODY_FONT,
          fontSize: 30,
          fontWeight: 800,
          lineHeight: 1.1,
          letterSpacing: 0.2,
          opacity: introOpacity,
          boxShadow: '0 7px 22px rgba(0, 0, 0, 0.25)',
        }}
      >
        Following the June 18 U.S.-Iran memorandum
      </div>

      <div
        style={{
          position: 'absolute',
          left: 96,
          right: 86,
          top: claimTop,
          zIndex: 12,
          color: IVORY,
          fontFamily: TITLE_FONT,
          fontSize: claimSize,
          fontWeight: 700,
          lineHeight: 0.96,
          letterSpacing: 1.1,
          opacity: introOpacity * claimOpacity,
          textShadow: '0 4px 18px rgba(0, 0, 0, 0.58)',
        }}
      >
        EIA REPORTED: TRAFFIC INCREASED
      </div>

      <div
        style={{
          position: 'absolute',
          left: 96,
          right: 86,
          top: 647,
          zIndex: 13,
          display: 'flex',
          alignItems: 'stretch',
          gap: 23,
          opacity: questionReveal,
          transform: `translate3d(0, ${interpolate(questionReveal, [0, 1], [18, 0], CLAMP)}px, 0)`,
        }}
      >
        <div style={{width: 6, backgroundColor: AMBER}} />
        <div
          style={{
            color: '#ffffff',
            fontFamily: TITLE_FONT,
            fontSize: 74,
            fontWeight: 700,
            lineHeight: 0.98,
            letterSpacing: 0.7,
            textShadow: '0 4px 20px rgba(0, 0, 0, 0.62)',
          }}
        >
          MOVEMENT OR RESTORED SUPPLY?
        </div>
      </div>

      <Caption visible={captionsVisible} text={caption} />
      <SourceFooter text={'Claim: U.S. EIA, July 7, 2026 | Context image: U.S. Navy / MC2 Indra Beaufort, Dec. 29, 2020, public domain'} />
    </AbsoluteFill>
  );
};

export const Motion_midform_16x9_S1_CHOKEPOINT_IN_VIEW: React.FC<VariantProps> = ({
  captionsVisible,
}) => {
  return (
    <AbsoluteFill style={{backgroundColor: INK, overflow: 'hidden'}}>
      <Sequence from={0} durationInFrames={TOTAL_FRAMES}>
        <AbsoluteFill>
          <Sequence from={0} durationInFrames={ORBIT_FRAMES}>
            <PersianGulfOrbit captionsVisible={captionsVisible} />
          </Sequence>
          <Sequence from={ORBIT_FRAMES} durationInFrames={MAP_FRAMES}>
            <StraitMap captionsVisible={captionsVisible} />
          </Sequence>
          <Sequence
            from={ORBIT_FRAMES + MAP_FRAMES}
            durationInFrames={VESSEL_FRAMES}
          >
            <TrafficToSupply captionsVisible={captionsVisible} />
          </Sequence>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
