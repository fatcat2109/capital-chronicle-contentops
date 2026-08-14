import React from 'react';
import {
  AbsoluteFill,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {VariantProps} from '../types';

const MAP_FRAMES = 102;
const VESSEL_FRAMES = 180;

const clamp = {
  extrapolateLeft: 'clamp' as const,
  extrapolateRight: 'clamp' as const,
};

const sourceStyle: React.CSSProperties = {
  position: 'absolute',
  left: 74,
  right: 74,
  bottom: 68,
  color: '#d8e1e4',
  fontFamily: '"Trebuchet MS", "Gill Sans", sans-serif',
  fontSize: 28,
  fontWeight: 400,
  lineHeight: 1.28,
  letterSpacing: 0.1,
  textShadow: '0 2px 10px rgba(0, 0, 0, 0.9)',
  zIndex: 8,
};

const Caption: React.FC<{
  children: React.ReactNode;
  placement: 'top' | 'bottom';
}> = ({children, placement}) => {
  return (
    <div
      style={{
        position: 'absolute',
        left: 70,
        right: 70,
        ...(placement === 'top' ? {top: 82} : {bottom: 315}),
        padding: '20px 24px',
        backgroundColor: 'rgba(5, 15, 21, 0.88)',
        borderLeft: '6px solid #40b6a4',
        color: '#ffffff',
        fontFamily: 'Georgia, "Times New Roman", serif',
        fontSize: 38,
        fontWeight: 700,
        lineHeight: 1.24,
        boxShadow: '0 12px 34px rgba(0, 0, 0, 0.28)',
        zIndex: 12,
      }}
    >
      {children}
    </div>
  );
};

const MapBeat: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  return (
    <AbsoluteFill
      data-beat-id="S1_SHORT_01_LOCATE_HORMUZ"
      style={{backgroundColor: '#dfe7e5', overflow: 'hidden'}}
    >
      <Img
        src={staticFile('assets/eia-hormuz-map-portrait.png')}
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: 'center center',
        }}
      />

      <AbsoluteFill
        style={{
          background:
            'radial-gradient(ellipse 250px 190px at 74% 57%, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.04) 45%, rgba(4,17,23,0.12) 69%, rgba(4,17,23,0.3) 100%)',
        }}
      />
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(4,14,20,0) 0%, rgba(4,14,20,0) 45%, rgba(4,14,20,0.74) 67%, rgba(4,14,20,0.92) 100%)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          left: 74,
          right: 74,
          top: 1050,
          paddingLeft: 28,
          borderLeft: '8px solid #39b5a0',
          color: '#f7f9f9',
          fontFamily: '"Trebuchet MS", "Gill Sans", sans-serif',
          textShadow: '0 3px 16px rgba(0, 0, 0, 0.72)',
          zIndex: 6,
        }}
      >
        <div
          style={{
            fontSize: 72,
            fontWeight: 800,
            lineHeight: 0.98,
            letterSpacing: 2.2,
          }}
        >
          OIL CHOKEPOINT
        </div>
        <div
          style={{
            marginTop: 18,
            color: '#8fe0d2',
            fontSize: 48,
            fontWeight: 700,
            lineHeight: 1.06,
            letterSpacing: 1.4,
          }}
        >
          STRAIT OF HORMUZ
        </div>
      </div>

      {captionsVisible ? (
        <Caption placement="bottom">
          Oil's supply story narrows here: the Strait of Hormuz.
        </Caption>
      ) : null}

      <div style={sourceStyle}>
        Source map: U.S. Energy Information Administration | Format-native
        render: Capital Chronicle
      </div>
    </AbsoluteFill>
  );
};

const VesselBeat: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const panEnd = Math.round(fps * 3.3);
  const objectPositionX = interpolate(frame, [0, panEnd], [62, 46], clamp);
  const eventOpacity = interpolate(frame, [8, 18], [0, 1], clamp);
  const eventOffset = interpolate(frame, [8, 18], [22, 0], clamp);
  const reportOpacity = interpolate(frame, [18, 30], [0, 1], clamp);
  const reportOffset = interpolate(frame, [18, 30], [28, 0], clamp);
  const boundaryOpacity = interpolate(frame, [103, 115], [0, 1], clamp);
  const boundaryOffset = interpolate(frame, [103, 115], [20, 0], clamp);

  return (
    <AbsoluteFill
      data-beat-id="S1_SHORT_02_REPORTED_TRAFFIC"
      style={{backgroundColor: '#07141c', overflow: 'hidden'}}
    >
      <Img
        src={staticFile('assets/usns-oiler-strait-of-hormuz.jpg')}
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: `${objectPositionX}% 50%`,
        }}
      />

      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(3,12,18,0.03) 0%, rgba(3,12,18,0.05) 37%, rgba(3,12,18,0.48) 58%, rgba(3,12,18,0.92) 100%)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          left: 74,
          right: 74,
          top: 842,
          display: 'flex',
          alignItems: 'stretch',
          opacity: eventOpacity,
          transform: `translateY(${eventOffset}px)`,
          zIndex: 6,
        }}
      >
        <div style={{width: 12, backgroundColor: '#41b8a5'}} />
        <div
          style={{
            flex: 1,
            padding: '22px 28px 24px',
            backgroundColor: 'rgba(8, 49, 53, 0.9)',
            color: '#f4fbfa',
            fontFamily: '"Trebuchet MS", "Gill Sans", sans-serif',
            fontSize: 37,
            fontWeight: 700,
            lineHeight: 1.18,
            letterSpacing: 0.2,
          }}
        >
          Reference event: June 18 U.S.-Iran memorandum
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          left: 74,
          right: 74,
          top: 1115,
          color: '#ffffff',
          fontFamily: '"Trebuchet MS", "Gill Sans", sans-serif',
          textShadow: '0 3px 18px rgba(0, 0, 0, 0.78)',
          opacity: reportOpacity,
          transform: `translateY(${reportOffset}px)`,
          zIndex: 6,
        }}
      >
        <div
          style={{
            fontSize: 68,
            fontWeight: 800,
            lineHeight: 0.98,
            letterSpacing: 1.4,
          }}
        >
          EIA REPORTED
          <br />
          TRAFFIC INCREASED
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          left: 74,
          right: 74,
          top: 1350,
          paddingTop: 22,
          borderTop: '3px solid rgba(116, 220, 202, 0.8)',
          color: '#8fe0d2',
          fontFamily: '"Trebuchet MS", "Gill Sans", sans-serif',
          fontSize: 48,
          fontWeight: 800,
          lineHeight: 1.04,
          letterSpacing: 0.8,
          textShadow: '0 3px 16px rgba(0, 0, 0, 0.84)',
          opacity: boundaryOpacity,
          transform: `translateY(${boundaryOffset}px)`,
          zIndex: 6,
        }}
      >
        NOT YET PROOF OF
        <br />
        RESTORED SUPPLY
      </div>

      {captionsVisible ? (
        <Caption placement="top">
          EIA reported increased Hormuz traffic after the June 18 U.S.-Iran
          memorandum. The question is whether those movements become restored
          supply.
        </Caption>
      ) : null}

      <div style={sourceStyle}>
        Claim: U.S. EIA, July 7, 2026 | Context image: U.S. Navy / MC2 Indra
        Beaufort, Dec. 29, 2020, public domain
      </div>
    </AbsoluteFill>
  );
};

export const Motion_short_9x16_S1_CHOKEPOINT_IN_VIEW: React.FC<VariantProps> = ({
  captionsVisible,
}) => {
  return (
    <AbsoluteFill style={{backgroundColor: '#07141c'}}>
      <Sequence from={0} durationInFrames={MAP_FRAMES}>
        <MapBeat captionsVisible={captionsVisible} />
      </Sequence>
      <Sequence from={MAP_FRAMES} durationInFrames={VESSEL_FRAMES}>
        <VesselBeat captionsVisible={captionsVisible} />
      </Sequence>
    </AbsoluteFill>
  );
};
