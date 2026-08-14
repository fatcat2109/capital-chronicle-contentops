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
import type {VariantProps} from '../types';

const palette = {
  ink: '#071519',
  white: '#f5f3ed',
  muted: '#c8d0ce',
  teal: '#13877d',
  amber: '#e8b95b',
};

const displayFont = 'Aptos Display, Franklin Gothic Medium, Trebuchet MS, sans-serif';
const textFont = 'Aptos, Trebuchet MS, sans-serif';

const bounded = (
  frame: number,
  inputRange: number[],
  outputRange: number[],
): number =>
  interpolate(frame, inputRange, outputRange, {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

type PhotoProps = {
  src: string;
  opacity?: number;
  objectPosition?: string;
  transform?: string;
  transformOrigin?: string;
  filter?: string;
  clipPath?: string;
};

const Photo: React.FC<PhotoProps> = ({
  src,
  opacity = 1,
  objectPosition = 'center',
  transform = 'none',
  transformOrigin = 'center',
  filter,
  clipPath,
}) => (
  <Img
    src={src}
    style={{
      position: 'absolute',
      width: '100%',
      height: '100%',
      objectFit: 'cover',
      objectPosition,
      opacity,
      transform,
      transformOrigin,
      filter,
      clipPath,
    }}
  />
);

const BottomWash: React.FC<{strength?: number}> = ({strength = 0.9}) => (
  <AbsoluteFill
    style={{
      background: `linear-gradient(180deg, rgba(5, 14, 18, 0.02) 25%, rgba(5, 14, 18, 0.42) 52%, rgba(5, 14, 18, ${strength}) 100%)`,
    }}
  />
);

const SourceLabel: React.FC<{text: string; opacity?: number}> = ({
  text,
  opacity = 1,
}) => (
  <div
    style={{
      position: 'absolute',
      left: 94,
      right: 94,
      bottom: 30,
      zIndex: 30,
      color: palette.muted,
      fontFamily: textFont,
      fontSize: 24,
      fontWeight: 500,
      lineHeight: 1.24,
      letterSpacing: 0.15,
      textShadow: '0 2px 9px rgba(0, 0, 0, 0.95)',
      opacity,
    }}
  >
    {text}
  </div>
);

const Caption: React.FC<{
  visible: boolean;
  text: string;
}> = ({visible, text}) => {
  if (!visible) {
    return null;
  }

  return (
    <div
      style={{
        position: 'absolute',
        left: 265,
        right: 265,
        bottom: 126,
        zIndex: 40,
        padding: '12px 20px 13px',
        color: palette.white,
        backgroundColor: 'rgba(3, 10, 13, 0.86)',
        borderLeft: `5px solid ${palette.amber}`,
        fontFamily: textFont,
        fontSize: 30,
        fontWeight: 650,
        lineHeight: 1.22,
        textAlign: 'center',
        boxShadow: '0 8px 30px rgba(0, 0, 0, 0.28)',
      }}
    >
      {text}
    </div>
  );
};

const BoundaryTag: React.FC<{
  text: string;
  style?: React.CSSProperties;
}> = ({text, style}) => (
  <div
    style={{
      position: 'absolute',
      top: 34,
      left: 94,
      zIndex: 24,
      padding: '8px 12px 7px',
      color: palette.white,
      backgroundColor: 'rgba(4, 18, 22, 0.74)',
      borderTop: `3px solid ${palette.amber}`,
      fontFamily: textFont,
      fontSize: 20,
      fontWeight: 750,
      lineHeight: 1,
      letterSpacing: 1.6,
      textTransform: 'uppercase',
      ...style,
    }}
  >
    {text}
  </div>
);

const TransitLimitBeat: React.FC<{captionsVisible: boolean}> = ({
  captionsVisible,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const linearPan = bounded(frame, [0, 139], [1.2, -4.2]);
  const tail = bounded(frame, [139, 149], [0, 1]);
  const drift = frame < 139 ? linearPan : -4.2 - 0.2 * (1 - (1 - tail) * (1 - tail));
  const labelIn = spring({
    fps,
    frame: frame - 7,
    config: {damping: 200, stiffness: 155, mass: 0.8},
  });

  return (
    <AbsoluteFill
      data-beat-id='S2_MID_B1_TRANSIT_LIMIT'
      style={{overflow: 'hidden', backgroundColor: palette.ink}}
    >
      <Photo
        src={staticFile('assets/commercial-tanker-oil-platform-persian-gulf.jpg')}
        objectPosition='51% 53%'
        transform={`scale(1.08) translateX(${drift}%)`}
        transformOrigin='51% 53%'
        filter='contrast(1.03) saturate(0.9)'
      />
      <BottomWash strength={0.94} />
      <BoundaryTag text='Archival context | March 28, 2009' />
      <div
        style={{
          position: 'absolute',
          left: 96,
          bottom: 232,
          zIndex: 20,
          width: 1240,
          color: palette.white,
          fontFamily: displayFont,
          fontSize: 94,
          fontWeight: 820,
          lineHeight: 0.98,
          letterSpacing: -2.7,
          textTransform: 'uppercase',
          textShadow: '0 5px 24px rgba(0, 0, 0, 0.65)',
          opacity: labelIn,
          transform: `translateY(${bounded(labelIn, [0, 1], [22, 0])}px)`,
        }}
      >
        TRANSIT IS NOT RESTORED SUPPLY
      </div>
      <div
        style={{
          position: 'absolute',
          left: 98,
          bottom: 207,
          zIndex: 21,
          width: 190,
          height: 6,
          backgroundColor: palette.amber,
          transform: `scaleX(${labelIn})`,
          transformOrigin: 'left center',
        }}
      />
      <SourceLabel text={`Archival context: U.S. Navy photo by Mass Communication Specialist 2nd Class Nathan Schaeffer, March 28, 2009 | Mechanism: Capital Chronicle`} />
      <Caption
        visible={captionsVisible}
        text={`A ship beyond Hormuz establishes transit, not restored supply. The barrels still have to reach shore.`}
      />
    </AbsoluteFill>
  );
};

const UnloadingChainBeat: React.FC<{captionsVisible: boolean}> = ({
  captionsVisible,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const imageIn = bounded(frame, [0, 6], [0, 1]);
  const headingIn = spring({
    fps,
    frame: frame - 8,
    config: {damping: 200, stiffness: 170, mass: 0.7},
  });
  const processProgress = bounded(frame, [25, 136], [0, 1]);
  const stations = [
    {label: '01 / UNLOAD', left: '63%', top: '29%', start: 26},
    {label: '02 / TERMINAL', left: '39%', top: '47%', start: 65},
    {label: '03 / PIPELINE', left: '16%', top: '65%', start: 104},
  ] as const;

  return (
    <AbsoluteFill
      data-beat-id='S2_MID_B2_UNLOADING_CHAIN'
      style={{overflow: 'hidden', backgroundColor: palette.ink}}
    >
      <Photo
        src={staticFile('assets/commercial-tanker-oil-platform-persian-gulf.jpg')}
        objectPosition='51% 53%'
        transform='scale(1.08) translateX(-4.4%)'
        filter='contrast(1.03) saturate(0.9)'
      />
      <Photo
        src={staticFile('assets/doe-tanker-terminal-pipeline.jpg')}
        objectPosition='49% 52%'
        opacity={imageIn}
        filter='contrast(1.04) saturate(0.82) brightness(0.88)'
      />
      <AbsoluteFill
        style={{
          background: 'linear-gradient(180deg, rgba(5, 14, 18, 0.34) 0%, rgba(5, 14, 18, 0.05) 37%, rgba(5, 14, 18, 0.86) 100%)',
        }}
      />
      <BoundaryTag
        text='Archival infrastructure | Not current throughput'
        style={{left: 'auto', right: 94}}
      />
      <div
        style={{
          position: 'absolute',
          left: 96,
          top: 82,
          zIndex: 22,
          color: palette.white,
          fontFamily: displayFont,
          fontSize: 62,
          fontWeight: 820,
          lineHeight: 1,
          letterSpacing: -1.1,
          textShadow: '0 4px 18px rgba(0, 0, 0, 0.82)',
          opacity: headingIn,
          transform: `translateX(${bounded(headingIn, [0, 1], [-24, 0])}px)`,
        }}
      >
        UNLOAD -&gt; TERMINAL -&gt; PIPELINE
      </div>
      <svg
        viewBox='0 0 1920 1080'
        preserveAspectRatio='none'
        style={{position: 'absolute', inset: 0, zIndex: 15}}
      >
        <path
          d='M 1345 375 C 1220 420, 1060 485, 890 550 S 590 680, 385 760'
          fill='none'
          stroke={palette.amber}
          strokeWidth={5}
          strokeLinecap='round'
          pathLength={100}
          strokeDasharray={100}
          strokeDashoffset={100 - processProgress * 100}
          opacity={0.92}
        />
      </svg>
      {stations.map((station) => {
        const phase = bounded(frame, [station.start, station.start + 7], [0, 1]);
        return (
          <div
            key={station.label}
            style={{
              position: 'absolute',
              left: station.left,
              top: station.top,
              zIndex: 20,
              padding: '10px 15px 9px',
              color: palette.white,
              backgroundColor: 'rgba(3, 17, 20, 0.86)',
              borderLeft: `5px solid ${palette.amber}`,
              fontFamily: textFont,
              fontSize: 25,
              fontWeight: 800,
              letterSpacing: 1.3,
              boxShadow: '0 7px 24px rgba(0, 0, 0, 0.3)',
              opacity: phase,
              transform: `translateY(${bounded(phase, [0, 1], [12, 0])}px)`,
            }}
          >
            {station.label}
          </div>
        );
      })}
      <SourceLabel
        opacity={bounded(frame, [3, 9], [0, 1])}
        text={`Archival context: U.S. Department of Energy, Strategic Petroleum Reserve image 011 | Mechanism: Capital Chronicle`}
      />
      <Caption
        visible={captionsVisible}
        text={`At the terminal, unloading connects the tanker to storage and pipelines: the bridge from movement to available oil.`}
      />
    </AbsoluteFill>
  );
};

const ProductionRestorationBeat: React.FC<{captionsVisible: boolean}> = ({
  captionsVisible,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const dissolve = bounded(frame, [0, 8], [0, 1]);
  const pipeFocus = bounded(frame, [34, 52], [0, 1]);
  const towerFocus = bounded(frame, [68, 88], [0, 1]);
  const headingIn = spring({
    fps,
    frame: frame - 18,
    config: {damping: 200, stiffness: 145, mass: 0.85},
  });
  const forecastIn = bounded(frame, [112, 130], [0, 1]);

  return (
    <AbsoluteFill
      data-beat-id='S2_MID_B3_PRODUCTION_RESTORATION'
      style={{overflow: 'hidden', backgroundColor: palette.ink}}
    >
      <Photo
        src={staticFile('assets/doe-tanker-terminal-pipeline.jpg')}
        objectPosition='49% 52%'
        filter='grayscale(1) contrast(1.05) brightness(0.66)'
      />
      <Photo
        src={staticFile('assets/nara-refinery-portrait.jpg')}
        objectPosition='50% 47%'
        opacity={dissolve}
        filter='grayscale(1) contrast(1.08) brightness(0.68)'
      />
      <Photo
        src={staticFile('assets/nara-refinery-portrait.jpg')}
        objectPosition='50% 47%'
        opacity={dissolve * pipeFocus}
        filter='grayscale(1) contrast(1.14) brightness(0.98)'
        clipPath='polygon(0 52%, 100% 47%, 100% 100%, 0 100%)'
      />
      <Photo
        src={staticFile('assets/nara-refinery-portrait.jpg')}
        objectPosition='50% 47%'
        opacity={dissolve * towerFocus}
        filter='grayscale(1) contrast(1.12) brightness(0.96)'
        clipPath='polygon(7% 0, 78% 0, 68% 69%, 0 72%, 0 10%)'
      />
      <AbsoluteFill
        style={{
          background: 'linear-gradient(180deg, rgba(4, 13, 16, 0.12) 0%, rgba(4, 13, 16, 0.05) 38%, rgba(4, 13, 16, 0.88) 100%)',
        }}
      />
      <BoundaryTag
        text='Historical refinery image | Forecast is source-bound'
        style={{left: 'auto', right: 94}}
      />
      <div
        style={{
          position: 'absolute',
          left: 96,
          right: 96,
          top: 94,
          zIndex: 25,
          padding: '19px 28px 18px',
          color: palette.white,
          backgroundColor: 'rgba(13, 135, 125, 0.94)',
          borderLeft: `8px solid ${palette.amber}`,
          fontFamily: displayFont,
          fontSize: 48,
          fontWeight: 830,
          lineHeight: 1.04,
          letterSpacing: -0.5,
          boxShadow: '0 12px 38px rgba(0, 0, 0, 0.35)',
          opacity: forecastIn,
          transform: `translateY(${bounded(forecastIn, [0, 1], [-12, 0])}px)`,
        }}
      >
        FORECAST - RESTORATION EXTENDS INTO Q1 2027
        <div
          style={{
            marginTop: 9,
            color: '#e8f2ef',
            fontFamily: textFont,
            fontSize: 20,
            fontWeight: 750,
            letterSpacing: 1.7,
          }}
        >
          U.S. EIA | JULY 7, 2026
        </div>
      </div>
      <div
        style={{
          position: 'absolute',
          left: 96,
          bottom: 250,
          zIndex: 20,
          width: 1120,
          color: palette.white,
          fontFamily: displayFont,
          fontSize: 88,
          fontWeight: 830,
          lineHeight: 0.98,
          letterSpacing: -2.2,
          textTransform: 'uppercase',
          textShadow: '0 5px 25px rgba(0, 0, 0, 0.78)',
          opacity: headingIn,
          transform: `translateX(${bounded(headingIn, [0, 1], [-24, 0])}px)`,
        }}
      >
        RESTORE SHUT-IN PRODUCTION
      </div>
      <SourceLabel text={`Archival context: U.S. National Archives / Office of War Information, NARA 535733 | Forecast: U.S. EIA, July 7, 2026`} />
      <Caption
        visible={captionsVisible}
        text={`Production has to return as well. EIA's forecast carries restoration of shut-in output into the first quarter of 2027.`}
      />
    </AbsoluteFill>
  );
};

const InventoryTestBeat: React.FC<{captionsVisible: boolean}> = ({
  captionsVisible,
}) => {
  const frame = useCurrentFrame();
  const finalHold = frame >= 159;
  const mainIn = bounded(frame, [4, 10], [0, 1]);
  const firstTankIn = bounded(frame, [20, 26], [0, 1]);
  const secondTankIn = bounded(frame, [32, 38], [0, 1]);
  const forecastIn = bounded(frame, [52, 58], [0, 1]);
  const labelsOut = bounded(frame, [136, 148], [1, 0]);

  return (
    <AbsoluteFill
      data-beat-id='S2_MID_B4_INVENTORY_TEST'
      style={{overflow: 'hidden', backgroundColor: palette.ink}}
    >
      <Photo
        src={staticFile('assets/refinery-storage-tanks.jpg')}
        objectPosition='52% 51%'
        filter='contrast(1.04) saturate(0.88) brightness(0.84)'
      />
      <AbsoluteFill
        style={{
          background: finalHold
            ? 'rgba(3, 13, 16, 0.68)'
            : 'linear-gradient(180deg, rgba(4, 14, 18, 0.12) 0%, rgba(4, 14, 18, 0.04) 40%, rgba(4, 14, 18, 0.9) 100%)',
        }}
      />
      {!finalHold ? (
        <>
          <BoundaryTag
            text='Context image | Not a measure of current stocks'
            style={{left: 'auto', right: 94}}
          />
          <div
            style={{
              position: 'absolute',
              left: '20%',
              top: '36%',
              zIndex: 18,
              padding: '9px 14px',
              color: palette.white,
              backgroundColor: 'rgba(3, 17, 20, 0.8)',
              borderTop: `4px solid ${palette.amber}`,
              fontFamily: textFont,
              fontSize: 21,
              fontWeight: 800,
              letterSpacing: 1.4,
              opacity: firstTankIn * labelsOut,
              transform: `translateY(${bounded(firstTankIn, [0, 1], [10, 0])}px)`,
            }}
          >
            STORAGE TANK
          </div>
          <div
            style={{
              position: 'absolute',
              left: '67%',
              top: '31%',
              zIndex: 18,
              padding: '9px 14px',
              color: palette.white,
              backgroundColor: 'rgba(3, 17, 20, 0.8)',
              borderTop: `4px solid ${palette.amber}`,
              fontFamily: textFont,
              fontSize: 21,
              fontWeight: 800,
              letterSpacing: 1.4,
              opacity: secondTankIn * labelsOut,
              transform: `translateY(${bounded(secondTankIn, [0, 1], [10, 0])}px)`,
            }}
          >
            TANK FIELD
          </div>
          <div
            style={{
              position: 'absolute',
              left: 96,
              right: 96,
              top: 92,
              zIndex: 24,
              padding: '17px 25px 16px',
              color: palette.white,
              backgroundColor: 'rgba(13, 135, 125, 0.94)',
              borderLeft: `8px solid ${palette.amber}`,
              fontFamily: displayFont,
              fontSize: 45,
              fontWeight: 830,
              lineHeight: 1.04,
              letterSpacing: -0.3,
              boxShadow: '0 12px 38px rgba(0, 0, 0, 0.34)',
              opacity: forecastIn * labelsOut,
              transform: `translateY(${bounded(forecastIn, [0, 1], [-10, 0])}px)`,
            }}
          >
            FORECAST - EIA EXPECTS BUILDS TO PRESSURE CRUDE LOWER
          </div>
          <div
            style={{
              position: 'absolute',
              left: 96,
              bottom: 250,
              zIndex: 20,
              width: 1480,
              color: palette.white,
              fontFamily: displayFont,
              fontSize: 88,
              fontWeight: 830,
              lineHeight: 0.98,
              letterSpacing: -2.2,
              textTransform: 'uppercase',
              textShadow: '0 5px 25px rgba(0, 0, 0, 0.78)',
              opacity: mainIn * labelsOut,
              transform: `translateX(${bounded(mainIn, [0, 1], [-22, 0])}px)`,
            }}
          >
            INVENTORIES ARE THE NEXT TEST
          </div>
        </>
      ) : (
        <div
          style={{
            position: 'absolute',
            left: 96,
            right: 96,
            top: 405,
            zIndex: 25,
            color: palette.white,
            fontFamily: displayFont,
            fontSize: 78,
            fontWeight: 840,
            lineHeight: 1.05,
            letterSpacing: -1.6,
            textAlign: 'center',
            textShadow: '0 5px 25px rgba(0, 0, 0, 0.8)',
          }}
        >
          NEXT: EIA RELEASE - JULY 7, 2026
          <div
            style={{
              width: 220,
              height: 7,
              margin: '25px auto 0',
              backgroundColor: palette.amber,
            }}
          />
        </div>
      )}
      <SourceLabel text={`Photo: Tony Webster, CC BY 4.0, via Wikimedia Commons; cropped/resized | Forecast: U.S. EIA, July 7, 2026`} />
      <Caption
        visible={captionsVisible}
        text={`Then inventories have to rebuild. EIA expects those builds to pressure crude lower. Now, the dated forecast.`}
      />
    </AbsoluteFill>
  );
};

export const Motion_midform_16x9_S2_FROM_TRANSIT_TO_BARRELS: React.FC<VariantProps> = ({
  captionsVisible,
}) => (
  <AbsoluteFill style={{overflow: 'hidden', backgroundColor: palette.ink}}>
    <Sequence from={0} durationInFrames={150}>
      <TransitLimitBeat captionsVisible={captionsVisible} />
    </Sequence>
    <Sequence from={150} durationInFrames={180}>
      <UnloadingChainBeat captionsVisible={captionsVisible} />
    </Sequence>
    <Sequence from={330} durationInFrames={210}>
      <ProductionRestorationBeat captionsVisible={captionsVisible} />
    </Sequence>
    <Sequence from={540} durationInFrames={195}>
      <InventoryTestBeat captionsVisible={captionsVisible} />
    </Sequence>
  </AbsoluteFill>
);
