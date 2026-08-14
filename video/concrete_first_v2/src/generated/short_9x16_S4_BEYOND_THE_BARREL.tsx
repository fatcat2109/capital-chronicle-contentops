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

const INK = '#071116';
const PAPER = '#f4f0e7';
const TEAL = '#138a7b';
const GOLD = '#e2ad43';
const DISPLAY = 'Franklin Gothic Medium, Trebuchet MS, sans-serif';
const BODY = 'Trebuchet MS, sans-serif';

const reveal = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, end], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

type BeatProps = {
  captionsVisible: boolean;
};

type SourceStripProps = {
  children: React.ReactNode;
};

const SourceStrip: React.FC<SourceStripProps> = ({children}) => (
  <div
    style={{
      position: 'absolute',
      left: 48,
      right: 48,
      bottom: 30,
      zIndex: 40,
      padding: '11px 15px 12px',
      borderLeft: `4px solid ${TEAL}`,
      background: 'linear-gradient(90deg, rgba(3,10,14,0.92) 0%, rgba(3,10,14,0.74) 72%, rgba(3,10,14,0.18) 100%)',
      color: '#dce3e3',
      fontFamily: BODY,
      fontSize: 23,
      lineHeight: 1.25,
      letterSpacing: 0.1,
      textShadow: '0 1px 2px rgba(0,0,0,0.8)',
    }}
  >
    {children}
  </div>
);

type CaptionProps = {
  text: string;
};

const Caption: React.FC<CaptionProps> = ({text}) => (
  <div
    style={{
      position: 'absolute',
      left: 48,
      right: 48,
      bottom: 330,
      zIndex: 50,
      padding: '15px 20px 17px',
      borderTop: `4px solid ${GOLD}`,
      backgroundColor: 'rgba(3,10,14,0.9)',
      color: PAPER,
      fontFamily: BODY,
      fontSize: 31,
      fontWeight: 700,
      lineHeight: 1.25,
      textAlign: 'center',
      textShadow: '0 2px 4px rgba(0,0,0,0.9)',
    }}
  >
    {text}
  </div>
);

const BeatOne: React.FC<BeatProps> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tilt = interpolate(frame, [0, 92], [28, -30], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const heading = reveal(frame, 0, 8);
  const q3 = spring({
    frame: frame - 5,
    fps,
    durationInFrames: 13,
    config: {damping: 18, stiffness: 180, mass: 0.7},
  });
  const q4 = spring({
    frame: frame - 15,
    fps,
    durationInFrames: 13,
    config: {damping: 18, stiffness: 180, mass: 0.7},
  });

  return (
    <AbsoluteFill style={{overflow: 'hidden', backgroundColor: INK, fontFamily: BODY}}>
      <Img
        src={staticFile('assets/nara-refinery-portrait.jpg')}
        style={{
          position: 'absolute',
          left: 0,
          top: '-5%',
          width: '100%',
          height: '110%',
          objectFit: 'cover',
          objectPosition: '50% 44%',
          transform: `translateY(${tilt}px) scale(1.015)`,
        }}
      />
      <AbsoluteFill
        style={{
          background: 'linear-gradient(180deg, rgba(3,10,14,0.78) 0%, rgba(3,10,14,0.06) 27%, rgba(3,10,14,0.16) 57%, rgba(3,10,14,0.93) 100%)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          top: 62,
          left: 54,
          right: 54,
          zIndex: 10,
          opacity: heading,
          transform: `translateY(${(1 - heading) * -12}px)`,
          display: 'flex',
          alignItems: 'center',
          gap: 18,
          paddingBottom: 18,
          borderBottom: '2px solid rgba(244,240,231,0.6)',
        }}
      >
        <div
          style={{
            color: PAPER,
            fontFamily: DISPLAY,
            fontSize: 70,
            fontWeight: 900,
            lineHeight: 0.95,
            letterSpacing: 1.2,
          }}
        >
          U.S. GASOLINE
        </div>
        <div
          style={{
            flexShrink: 0,
            padding: '10px 15px 11px',
            backgroundColor: TEAL,
            color: '#ffffff',
            fontFamily: DISPLAY,
            fontSize: 27,
            fontWeight: 900,
            letterSpacing: 1.8,
          }}
        >
          FORECAST
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          left: 52,
          top: 588,
          zIndex: 12,
          width: 430,
          padding: '19px 22px 20px',
          borderLeft: `7px solid ${TEAL}`,
          background: 'linear-gradient(90deg, rgba(3,10,14,0.9), rgba(3,10,14,0.58))',
          opacity: q3,
          transform: `translateX(${(1 - q3) * -38}px)`,
          color: PAPER,
          textShadow: '0 2px 4px rgba(0,0,0,0.9)',
        }}
      >
        <div style={{fontSize: 25, fontWeight: 900, letterSpacing: 2.2, color: '#8dd5cb'}}>
          FORECAST / Q3 2026
        </div>
        <div style={{fontFamily: DISPLAY, fontSize: 101, fontWeight: 900, lineHeight: 1, marginTop: 8}}>
          $3.80
        </div>
      </div>
      <div
        style={{
          position: 'absolute',
          left: 482,
          top: 696,
          zIndex: 11,
          width: 174,
          height: 3,
          backgroundColor: '#8dd5cb',
          transformOrigin: 'left center',
          transform: `scaleX(${q3})`,
          boxShadow: '0 1px 4px rgba(0,0,0,0.8)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          right: 48,
          top: 905,
          zIndex: 12,
          width: 432,
          padding: '19px 22px 20px',
          borderRight: `7px solid ${GOLD}`,
          background: 'linear-gradient(270deg, rgba(3,10,14,0.92), rgba(3,10,14,0.56))',
          opacity: q4,
          transform: `translateX(${(1 - q4) * 38}px)`,
          color: PAPER,
          textAlign: 'right',
          textShadow: '0 2px 4px rgba(0,0,0,0.9)',
        }}
      >
        <div style={{fontSize: 25, fontWeight: 900, letterSpacing: 2.2, color: '#f0c66f'}}>
          FORECAST / Q4 2026
        </div>
        <div style={{fontFamily: DISPLAY, fontSize: 101, fontWeight: 900, lineHeight: 1, marginTop: 8}}>
          $3.40
        </div>
      </div>
      <div
        style={{
          position: 'absolute',
          right: 480,
          top: 1013,
          zIndex: 11,
          width: 154,
          height: 3,
          backgroundColor: '#f0c66f',
          transformOrigin: 'right center',
          transform: `scaleX(${q4})`,
          boxShadow: '0 1px 4px rgba(0,0,0,0.8)',
        }}
      />

      {captionsVisible ? (
        <Caption text={'EIA forecasts gasoline at $3.80 in Q3 and $3.40 in Q4.'} />
      ) : null}
      <SourceStrip>
        Forecast: U.S. Energy Information Administration, July 7, 2026 |
        <br />
        Image: U.S. National Archives / Office of War Information, NARA 535733
      </SourceStrip>
    </AbsoluteFill>
  );
};

const BeatTwo: React.FC<BeatProps> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const imageDrift = interpolate(frame, [0, 74], [3, -4], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const firstLine = reveal(frame, 0, 9);
  const secondLine = reveal(frame, 6, 15);

  return (
    <AbsoluteFill style={{overflow: 'hidden', backgroundColor: INK, fontFamily: BODY}}>
      <Img
        src={staticFile('assets/refinery-storage-tanks.jpg')}
        style={{
          position: 'absolute',
          left: '-3%',
          top: '-2%',
          width: '106%',
          height: '104%',
          objectFit: 'cover',
          objectPosition: '58% 51%',
          transform: `translateY(${imageDrift}px) scale(1.02)`,
        }}
      />
      <AbsoluteFill
        style={{
          background: 'linear-gradient(180deg, rgba(3,10,14,0.08) 0%, rgba(3,10,14,0.03) 34%, rgba(3,10,14,0.5) 60%, rgba(3,10,14,0.9) 100%)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          left: 53,
          right: 44,
          top: 805,
          zIndex: 12,
          padding: '26px 24px 30px',
          borderLeft: `8px solid ${GOLD}`,
          background: 'linear-gradient(90deg, rgba(3,10,14,0.86) 0%, rgba(3,10,14,0.54) 72%, rgba(3,10,14,0.05) 100%)',
          color: PAPER,
          textShadow: '0 3px 7px rgba(0,0,0,0.95)',
        }}
      >
        <div
          style={{
            overflow: 'hidden',
            clipPath: `inset(0 ${100 - firstLine * 100}% 0 0)`,
            fontFamily: DISPLAY,
            fontSize: 66,
            fontWeight: 900,
            lineHeight: 1.03,
            letterSpacing: 0.4,
            whiteSpace: 'nowrap',
          }}
        >
          A DECLINE CAN STILL LAND
        </div>
        <div
          style={{
            marginTop: 22,
            overflow: 'hidden',
            clipPath: `inset(0 ${100 - secondLine * 100}% 0 0)`,
            fontFamily: DISPLAY,
            fontSize: 74,
            fontWeight: 900,
            lineHeight: 1.02,
            letterSpacing: 0.2,
            whiteSpace: 'pre-line',
          }}
        >
          {'ABOVE PRIOR-CYCLE\nAVERAGES'}
        </div>
      </div>

      {captionsVisible ? (
        <Caption text={'Even a decline can leave oil above prior-cycle averages.'} />
      ) : null}
      <SourceStrip>
        Analysis: Capital Chronicle | Image: Tony Webster, CC BY 4.0,
        <br />
        via Wikimedia Commons; cropped/resized
      </SourceStrip>
    </AbsoluteFill>
  );
};

const BeatThree: React.FC<BeatProps> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const pan = interpolate(frame, [0, 70], [56, -48], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const importer = reveal(frame, 4, 13);
  const producer = reveal(frame, 34, 44);
  const yieldBoundary = reveal(frame, 72, 81);

  return (
    <AbsoluteFill style={{overflow: 'hidden', backgroundColor: INK, fontFamily: BODY}}>
      <Img
        src={staticFile('assets/commercial-tanker-oil-platform-persian-gulf.jpg')}
        style={{
          position: 'absolute',
          left: '-11%',
          top: '-3%',
          width: '122%',
          height: '106%',
          objectFit: 'cover',
          objectPosition: '47% 48%',
          transform: `translateX(${pan}px) scale(1.025)`,
        }}
      />
      <AbsoluteFill
        style={{
          background: 'linear-gradient(180deg, rgba(3,10,14,0.55) 0%, rgba(3,10,14,0.02) 30%, rgba(3,10,14,0.16) 52%, rgba(3,10,14,0.92) 100%)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          top: 62,
          left: 52,
          zIndex: 15,
          padding: '9px 14px 10px',
          borderLeft: `6px solid ${GOLD}`,
          backgroundColor: 'rgba(3,10,14,0.78)',
          color: PAPER,
          fontSize: 27,
          fontWeight: 900,
          letterSpacing: 2,
        }}
      >
        CONDITIONAL / IF THE RETREAT IS SUSTAINED
      </div>

      <div
        style={{
          position: 'absolute',
          right: 54,
          top: 500,
          zIndex: 12,
          width: 480,
          padding: '18px 21px 20px',
          borderRight: `7px solid ${GOLD}`,
          background: 'linear-gradient(270deg, rgba(3,10,14,0.9), rgba(3,10,14,0.46))',
          color: PAPER,
          textAlign: 'right',
          opacity: producer,
          transform: `translateX(${(1 - producer) * 46}px)`,
          textShadow: '0 3px 6px rgba(0,0,0,0.9)',
        }}
      >
        <div style={{fontSize: 27, fontWeight: 900, letterSpacing: 1.8, color: '#f0c66f'}}>
          PRODUCER REVENUE
        </div>
        <div style={{fontFamily: DISPLAY, fontSize: 59, fontWeight: 900, lineHeight: 0.98, marginTop: 10}}>
          POSSIBLE
          <br />
          PRESSURE
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          left: 54,
          top: 866,
          zIndex: 12,
          width: 455,
          padding: '18px 21px 20px',
          borderLeft: `7px solid ${TEAL}`,
          background: 'linear-gradient(90deg, rgba(3,10,14,0.9), rgba(3,10,14,0.44))',
          color: PAPER,
          opacity: importer,
          transform: `translateX(${(1 - importer) * -46}px)`,
          textShadow: '0 3px 6px rgba(0,0,0,0.9)',
        }}
      >
        <div style={{fontSize: 27, fontWeight: 900, letterSpacing: 1.8, color: '#8dd5cb'}}>
          IMPORTERS
        </div>
        <div style={{fontFamily: DISPLAY, fontSize: 62, fontWeight: 900, lineHeight: 0.98, marginTop: 10}}>
          POSSIBLE
          <br />
          SUPPORT
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          left: 54,
          right: 54,
          top: 1275,
          zIndex: 14,
          padding: '20px 0 22px',
          borderTop: `4px solid ${GOLD}`,
          borderBottom: '1px solid rgba(244,240,231,0.5)',
          background: 'linear-gradient(90deg, rgba(3,10,14,0.92), rgba(3,10,14,0.66), rgba(3,10,14,0.92))',
          color: PAPER,
          opacity: yieldBoundary,
          transform: `translateY(${(1 - yieldBoundary) * 20}px)`,
          textAlign: 'center',
          textShadow: '0 3px 6px rgba(0,0,0,0.95)',
        }}
      >
        <div style={{fontSize: 29, fontWeight: 900, letterSpacing: 2.5}}>
          LONG-TERM YIELDS
        </div>
        <div style={{fontFamily: DISPLAY, fontSize: 67, fontWeight: 900, lineHeight: 1, marginTop: 7, color: '#f0c66f'}}>
          NO GUARANTEE
        </div>
      </div>

      {captionsVisible ? (
        <Caption text={'Importers may benefit; producer revenues may weaken. Long-term yields are not guaranteed.'} />
      ) : null}
      <SourceStrip>
        Analysis: Capital Chronicle | Image: U.S. Navy photo by MC2 Nathan
        <br />
        Schaeffer, March 28, 2009
      </SourceStrip>
    </AbsoluteFill>
  );
};

const BeatFour: React.FC<BeatProps> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const moveX = interpolate(frame, [0, 45], [-28, 18], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const moveY = interpolate(frame, [0, 45], [24, -20], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const boundary = reveal(frame, 37, 45);
  const prices = reveal(frame, 46, 53);
  const labor = reveal(frame, 52, 59);
  const expectations = reveal(frame, 58, 65);
  const question = reveal(frame, 66, 73);

  return (
    <AbsoluteFill style={{overflow: 'hidden', backgroundColor: INK, fontFamily: BODY}}>
      <Img
        src={staticFile('assets/doe-tanker-terminal-pipeline.jpg')}
        style={{
          position: 'absolute',
          left: '-7%',
          top: '-5%',
          width: '114%',
          height: '110%',
          objectFit: 'cover',
          objectPosition: '54% 52%',
          transform: `translate(${moveX}px, ${moveY}px) scale(1.025)`,
        }}
      />
      <AbsoluteFill
        style={{
          background: 'linear-gradient(180deg, rgba(3,10,14,0.7) 0%, rgba(3,10,14,0.12) 35%, rgba(3,10,14,0.28) 61%, rgba(3,10,14,0.94) 100%)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          top: 58,
          left: 52,
          zIndex: 12,
          padding: '8px 14px 9px',
          borderLeft: `6px solid ${GOLD}`,
          backgroundColor: 'rgba(3,10,14,0.78)',
          color: PAPER,
          fontSize: 26,
          fontWeight: 900,
          letterSpacing: 2.3,
          opacity: boundary,
        }}
      >
        POLICY BOUNDARY
      </div>

      <div
        style={{
          position: 'absolute',
          left: 52,
          right: 52,
          top: 135,
          zIndex: 12,
          paddingBottom: 18,
          borderBottom: `4px solid ${TEAL}`,
          color: PAPER,
          fontFamily: DISPLAY,
          fontSize: 79,
          fontWeight: 900,
          lineHeight: 0.96,
          letterSpacing: 0.5,
          opacity: boundary,
          transform: `translateY(${(1 - boundary) * -18}px)`,
          textShadow: '0 3px 7px rgba(0,0,0,0.95)',
        }}
      >
        NO AUTOMATIC
        <br />
        FED MOVE
      </div>

      <div
        style={{
          position: 'absolute',
          left: 54,
          top: 615,
          zIndex: 13,
          width: 450,
          padding: '11px 17px 12px',
          borderBottom: `5px solid ${TEAL}`,
          background: 'linear-gradient(90deg, rgba(3,10,14,0.88), rgba(3,10,14,0.32))',
          color: PAPER,
          fontFamily: DISPLAY,
          fontSize: 44,
          fontWeight: 900,
          letterSpacing: 1,
          opacity: prices,
          transform: `translateX(${(1 - prices) * -30}px)`,
          textShadow: '0 2px 5px rgba(0,0,0,0.9)',
        }}
      >
        BROADER PRICES
      </div>

      <div
        style={{
          position: 'absolute',
          right: 76,
          top: 790,
          zIndex: 13,
          width: 320,
          padding: '11px 17px 12px',
          borderBottom: `5px solid ${GOLD}`,
          background: 'linear-gradient(270deg, rgba(3,10,14,0.88), rgba(3,10,14,0.32))',
          color: PAPER,
          fontFamily: DISPLAY,
          fontSize: 48,
          fontWeight: 900,
          letterSpacing: 1,
          textAlign: 'right',
          opacity: labor,
          transform: `translateX(${(1 - labor) * 30}px)`,
          textShadow: '0 2px 5px rgba(0,0,0,0.9)',
        }}
      >
        LABOR
      </div>

      <div
        style={{
          position: 'absolute',
          left: 162,
          top: 951,
          zIndex: 13,
          width: 600,
          padding: '11px 17px 12px',
          borderBottom: '5px solid #b7c7ca',
          background: 'linear-gradient(90deg, rgba(3,10,14,0.82), rgba(3,10,14,0.28))',
          color: PAPER,
          fontFamily: DISPLAY,
          fontSize: 47,
          fontWeight: 900,
          letterSpacing: 0.7,
          opacity: expectations,
          transform: `translateY(${(1 - expectations) * 20}px)`,
          textShadow: '0 2px 5px rgba(0,0,0,0.9)',
        }}
      >
        EXPECTATIONS
      </div>

      <div
        style={{
          position: 'absolute',
          left: 52,
          right: 52,
          top: 1198,
          zIndex: 15,
          padding: '22px 24px 25px',
          borderLeft: `8px solid ${GOLD}`,
          background: 'linear-gradient(90deg, rgba(3,10,14,0.94), rgba(3,10,14,0.68))',
          color: PAPER,
          opacity: question,
          transform: `translateY(${(1 - question) * 24}px)`,
          textShadow: '0 3px 7px rgba(0,0,0,0.95)',
        }}
      >
        <div style={{fontSize: 25, fontWeight: 900, letterSpacing: 3, color: '#f0c66f'}}>
          NEXT
        </div>
        <div style={{fontFamily: DISPLAY, fontSize: 55, fontWeight: 900, lineHeight: 1.02, marginTop: 9}}>
          WHAT CONFIRMS OR
          <br />
          CHALLENGES THE PATH?
        </div>
      </div>

      {captionsVisible ? (
        <Caption text={'Cheaper gasoline may ease headline inflation, not dictate the Fed. What confirms it?'} />
      ) : null}
      <SourceStrip>
        Policy boundary: Federal Reserve, June 17, 2026; Capital Chronicle |
        <br />
        Image: U.S. Department of Energy, Strategic Petroleum Reserve image 011
      </SourceStrip>
    </AbsoluteFill>
  );
};

export const Motion_short_9x16_S4_BEYOND_THE_BARREL: React.FC<VariantProps> = ({
  captionsVisible,
}) => (
  <AbsoluteFill style={{backgroundColor: INK}}>
    <Sequence from={0} durationInFrames={93} name={'S4_SHORT_01'}>
      <BeatOne captionsVisible={Boolean(captionsVisible)} />
    </Sequence>
    <Sequence from={93} durationInFrames={75} name={'S4_SHORT_02'}>
      <BeatTwo captionsVisible={Boolean(captionsVisible)} />
    </Sequence>
    <Sequence from={168} durationInFrames={102} name={'S4_SHORT_03'}>
      <BeatThree captionsVisible={Boolean(captionsVisible)} />
    </Sequence>
    <Sequence from={270} durationInFrames={90} name={'S4_SHORT_04'}>
      <BeatFour captionsVisible={Boolean(captionsVisible)} />
    </Sequence>
  </AbsoluteFill>
);
