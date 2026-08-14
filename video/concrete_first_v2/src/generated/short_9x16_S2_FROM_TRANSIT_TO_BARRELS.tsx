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
import {VariantProps} from '../types';

const COLORS = {
  white: '#f6f3ed',
  muted: '#c5ced5',
  ink: '#071116',
  teal: '#168777',
};

const ramp = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, end], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

const smoothRamp = (frame: number, start: number, end: number) => {
  const value = ramp(frame, start, end);
  return value * value * (3 - 2 * value);
};

const imageStyle: React.CSSProperties = {
  position: 'absolute',
  inset: 0,
  width: '100%',
  height: '100%',
  objectFit: 'cover',
  userSelect: 'none',
};

const vignetteStyle: React.CSSProperties = {
  background:
    'linear-gradient(180deg, rgba(3,10,14,0.08) 0%, rgba(3,10,14,0.02) 35%, rgba(3,10,14,0.56) 64%, rgba(3,10,14,0.91) 100%)',
};

const SourceLabel: React.FC<{text: string; opacity?: number}> = ({
  text,
  opacity = 1,
}) => (
  <div
    style={{
      position: 'absolute',
      left: 76,
      right: 68,
      bottom: 72,
      color: COLORS.muted,
      fontFamily: 'Helvetica Neue, Helvetica, sans-serif',
      fontSize: 24,
      fontWeight: 400,
      lineHeight: 1.24,
      letterSpacing: 0.1,
      opacity,
      textShadow: '0 2px 8px rgba(0,0,0,0.92)',
    }}
  >
    {text}
  </div>
);

const Caption: React.FC<{
  visible: boolean;
  text: string;
  opacity?: number;
}> = ({visible, text, opacity = 1}) => {
  if (!visible) {
    return null;
  }

  return (
    <div
      style={{
        position: 'absolute',
        left: 76,
        right: 76,
        bottom: 330,
        display: 'flex',
        justifyContent: 'center',
        opacity,
      }}
    >
      <div
        style={{
          maxWidth: 900,
          padding: '15px 22px 17px',
          backgroundColor: 'rgba(3,10,14,0.88)',
          color: COLORS.white,
          fontFamily: 'Helvetica Neue, Helvetica, sans-serif',
          fontSize: 34,
          fontWeight: 600,
          lineHeight: 1.24,
          textAlign: 'center',
          boxShadow: '0 8px 28px rgba(0,0,0,0.28)',
        }}
      >
        {text}
      </div>
    </div>
  );
};

const MainLabel: React.FC<{
  text: string;
  top: number;
  opacity: number;
}> = ({text, top, opacity}) => (
  <div
    style={{
      position: 'absolute',
      left: 76,
      right: 56,
      top,
      color: COLORS.white,
      fontFamily: 'Helvetica Neue, Helvetica, sans-serif',
      fontSize: 70,
      fontWeight: 800,
      lineHeight: 1.02,
      letterSpacing: -1.8,
      opacity,
      textShadow: '0 3px 18px rgba(0,0,0,0.9)',
    }}
  >
    {text}
  </div>
);

const EvidenceBanner: React.FC<{
  frame: number;
  start: number;
  top: number;
  text: string;
  opacity?: number;
}> = ({frame, start, top, text, opacity = 1}) => {
  const {fps} = useVideoConfig();
  const reveal = spring({
    fps,
    frame: Math.max(0, frame - start),
    durationInFrames: 14,
    config: {
      damping: 200,
      mass: 0.7,
      stiffness: 180,
    },
  });

  return (
    <div
      style={{
        position: 'absolute',
        left: 76,
        right: 76,
        top,
        minHeight: 190,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '22px 30px',
        boxSizing: 'border-box',
        borderRadius: 20,
        backgroundColor: COLORS.teal,
        color: COLORS.white,
        fontFamily: 'Helvetica Neue, Helvetica, sans-serif',
        fontSize: 39,
        fontWeight: 800,
        lineHeight: 1.17,
        letterSpacing: 0.2,
        textAlign: 'center',
        opacity: reveal * opacity,
        transform: `translate3d(0, ${(1 - reveal) * 24}px, 0)`,
        boxShadow: '0 14px 36px rgba(0,0,0,0.28)',
      }}
    >
      {text}
    </div>
  );
};

const TerminalBeat: React.FC<{captionsVisible: boolean}> = ({
  captionsVisible,
}) => {
  const frame = useCurrentFrame();
  const travel = smoothRamp(frame, 0, 72);
  const settle = smoothRamp(frame, 72, 78);
  const translateX = 28 - travel * 56 - settle * 4;
  const labelOpacity = ramp(frame, 3, 11);
  const sourceOpacity = ramp(frame, 0, 6);

  return (
    <AbsoluteFill
      data-beat-id='S2_SHORT_B1_TERMINAL'
      style={{backgroundColor: COLORS.ink, overflow: 'hidden'}}
    >
      <Img
        src={staticFile('assets/doe-tanker-terminal-pipeline.jpg')}
        style={{
          ...imageStyle,
          objectPosition: '48% 53%',
          transformOrigin: '48% 53%',
          transform: `translate3d(${translateX}px, 0, 0) scale(1.08)`,
        }}
      />
      <AbsoluteFill style={vignetteStyle} />
      <MainLabel
        text='AFTER HORMUZ: OIL MUST REACH SHORE'
        top={1124}
        opacity={labelOpacity}
      />
      <Caption
        visible={captionsVisible}
        text='After Hormuz, oil still has to reach the terminal.'
        opacity={labelOpacity}
      />
      <SourceLabel
        opacity={sourceOpacity}
        text='Archival context: U.S. Department of Energy, Strategic Petroleum Reserve image 011 | Mechanism: Capital Chronicle'
      />
    </AbsoluteFill>
  );
};

const ProductionBeat: React.FC<{captionsVisible: boolean}> = ({
  captionsVisible,
}) => {
  const frame = useCurrentFrame();
  const dissolve = ramp(frame, 0, 8);
  const tilt = smoothRamp(frame, 4, 78);
  const translateY = -46 + tilt * 66;
  const labelOpacity = ramp(frame, 10, 20);
  const sourceOpacity = ramp(frame, 6, 14);

  return (
    <AbsoluteFill
      data-beat-id='S2_SHORT_B2_PRODUCTION'
      style={{backgroundColor: COLORS.ink, overflow: 'hidden'}}
    >
      <AbsoluteFill style={{opacity: dissolve}}>
        <Img
          src={staticFile('assets/nara-refinery-portrait.jpg')}
          style={{
            ...imageStyle,
            objectPosition: '51% 48%',
            transformOrigin: '51% 48%',
            transform: `translate3d(0, ${translateY}px, 0) scale(1.1)`,
          }}
        />
        <AbsoluteFill style={vignetteStyle} />
        <EvidenceBanner
          frame={frame}
          start={35}
          top={332}
          text='FORECAST - RESTORATION EXTENDS INTO Q1 2027'
        />
        <MainLabel
          text='RESTORE SHUT-IN PRODUCTION'
          top={1078}
          opacity={labelOpacity}
        />
        <Caption
          visible={captionsVisible}
          text='EIA carries shut-in production restoration into the first quarter of 2027.'
          opacity={labelOpacity}
        />
        <SourceLabel
          opacity={sourceOpacity}
          text='Archival context: U.S. National Archives / Office of War Information, NARA 535733 | Forecast: U.S. EIA, July 7, 2026'
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const InventoryBeat: React.FC<{captionsVisible: boolean}> = ({
  captionsVisible,
}) => {
  const frame = useCurrentFrame();
  const cutIn = ramp(frame, 0, 4);
  const expansion = smoothRamp(frame, 3, 84);
  const scale = 1.15 - expansion * 0.11;
  const contentOut = 1 - ramp(frame, 88, 96);
  const dateOpacity = ramp(frame, 94, 99);
  const dateShift = 18 * (1 - smoothRamp(frame, 94, 101));
  const labelOpacity = ramp(frame, 6, 15) * contentOut;
  const sourceOpacity = ramp(frame, 2, 9);

  return (
    <AbsoluteFill
      data-beat-id='S2_SHORT_B3_INVENTORIES'
      style={{backgroundColor: COLORS.ink, overflow: 'hidden'}}
    >
      <AbsoluteFill style={{opacity: cutIn}}>
        <Img
          src={staticFile('assets/refinery-storage-tanks.jpg')}
          style={{
            ...imageStyle,
            objectPosition: '56% 50%',
            transformOrigin: '56% 50%',
            transform: `scale(${scale})`,
          }}
        />
        <AbsoluteFill style={vignetteStyle} />
        <AbsoluteFill
          style={{
            backgroundColor: `rgba(3,10,14,${dateOpacity * 0.28})`,
          }}
        />
        <EvidenceBanner
          frame={frame}
          start={16}
          top={286}
          text='FORECAST - EIA EXPECTS BUILDS TO PRESSURE CRUDE LOWER'
          opacity={contentOut}
        />
        <MainLabel
          text='REBUILD INVENTORIES'
          top={1038}
          opacity={labelOpacity}
        />
        <div
          style={{
            position: 'absolute',
            left: 76,
            right: 70,
            top: 704,
            paddingTop: 28,
            borderTop: `5px solid ${COLORS.teal}`,
            color: COLORS.white,
            fontFamily: 'Helvetica Neue, Helvetica, sans-serif',
            fontSize: 61,
            fontWeight: 800,
            lineHeight: 1.08,
            letterSpacing: -1.1,
            opacity: dateOpacity,
            transform: `translate3d(0, ${dateShift}px, 0)`,
            textShadow: '0 3px 20px rgba(0,0,0,0.95)',
          }}
        >
          NEXT: EIA RELEASE - JULY 7, 2026
        </div>
        <Caption
          visible={captionsVisible}
          text='EIA expects inventory builds to pressure crude lower. Next: its dated forecast.'
          opacity={ramp(frame, 5, 14)}
        />
        <SourceLabel
          opacity={sourceOpacity}
          text='Photo: Tony Webster, CC BY 4.0, via Wikimedia Commons; cropped/resized | Forecast: U.S. EIA, July 7, 2026'
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Motion_short_9x16_S2_FROM_TRANSIT_TO_BARRELS: React.FC<
  VariantProps
> = ({captionsVisible}) => (
  <AbsoluteFill
    data-duration-frames={324}
    style={{backgroundColor: COLORS.ink, overflow: 'hidden'}}
  >
    <Sequence from={0} durationInFrames={96}>
      <TerminalBeat captionsVisible={captionsVisible === true} />
    </Sequence>
    <Sequence from={96} durationInFrames={114}>
      <ProductionBeat captionsVisible={captionsVisible === true} />
    </Sequence>
    <Sequence from={210} durationInFrames={114}>
      <InventoryBeat captionsVisible={captionsVisible === true} />
    </Sequence>
  </AbsoluteFill>
);
