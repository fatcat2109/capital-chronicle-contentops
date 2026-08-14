import React from 'react';
import {
  AbsoluteFill,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import type {VariantProps} from '../types';

const FONT = 'Franklin Gothic Medium, Arial Narrow, sans-serif';
const BODY_FONT = 'Trebuchet MS, sans-serif';
const INK = '#071412';
const PAPER = '#f4f1e8';
const MUTED = '#bfc9c5';
const TEAL = '#19a98f';
const AMBER = '#e4b45d';
const CLAMP = {
  extrapolateLeft: 'clamp' as const,
  extrapolateRight: 'clamp' as const,
};

const reveal = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, end], [0, 1], CLAMP);

const SourceStrip: React.FC<{text: string}> = ({text}) => (
  <div
    style={{
      position: 'absolute',
      left: 0,
      right: 0,
      bottom: 0,
      minHeight: 82,
      zIndex: 40,
      display: 'flex',
      alignItems: 'flex-end',
      padding: '22px 72px 17px',
      boxSizing: 'border-box',
      background: 'linear-gradient(180deg, rgba(3,12,11,0), rgba(3,12,11,0.94) 58%)',
      color: MUTED,
      fontFamily: BODY_FONT,
      fontSize: 20,
      lineHeight: 1.2,
      letterSpacing: 0.1,
      textShadow: '0 1px 3px rgba(0,0,0,0.85)',
    }}
  >
    <div style={{maxWidth: 1776}}>{text}</div>
  </div>
);

const Caption: React.FC<{visible: boolean; text: string}> = ({visible, text}) => {
  if (!visible) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: '50%',
        bottom: 126,
        zIndex: 45,
        width: '76%',
        transform: 'translateX(-50%)',
        boxSizing: 'border-box',
        padding: '12px 22px 13px',
        borderTop: `3px solid ${TEAL}`,
        background: 'rgba(4,14,13,0.92)',
        color: PAPER,
        fontFamily: BODY_FONT,
        fontSize: 26,
        fontWeight: 700,
        lineHeight: 1.22,
        textAlign: 'center',
        boxShadow: '0 10px 28px rgba(0,0,0,0.34)',
      }}
    >
      {text}
    </div>
  );
};

const TankForecast: React.FC<{
  left: number;
  top: number;
  quarter: string;
  value: string;
  opacity: number;
  rise: number;
}> = ({left, top, quarter, value, opacity, rise}) => (
  <div
    style={{
      position: 'absolute',
      left,
      top,
      width: 390,
      opacity,
      transform: `translateY(${rise}px)`,
      color: PAPER,
      fontFamily: FONT,
      textShadow: '0 3px 10px rgba(0,0,0,0.8)',
    }}
  >
    <div
      style={{
        display: 'inline-block',
        padding: '7px 12px 6px',
        background: TEAL,
        color: '#f8fffc',
        fontSize: 21,
        fontWeight: 900,
        letterSpacing: 2.2,
      }}
    >
      EIA FORECAST
    </div>
    <div
      style={{
        marginTop: 8,
        padding: '15px 18px 16px',
        borderLeft: `6px solid ${TEAL}`,
        background: 'rgba(4,14,13,0.8)',
        boxShadow: '0 12px 30px rgba(0,0,0,0.25)',
      }}
    >
      <div style={{fontSize: 30, fontWeight: 800, letterSpacing: 1.6}}>{quarter}</div>
      <div style={{marginTop: 1, fontSize: 72, fontWeight: 900, lineHeight: 0.98}}>{value}</div>
    </div>
    <div style={{width: 88, height: 4, marginLeft: 6, background: TEAL}} />
  </div>
);

const S4Mid01: React.FC<{captionsVisible?: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const track = interpolate(frame, [0, 135], [0, -76], CLAMP);
  const headingIn = reveal(frame, 0, 12);
  const headingSpring = spring({
    frame,
    fps: 30,
    config: {damping: 24, mass: 0.65, stiffness: 170},
  });
  const headingY = interpolate(headingSpring, [0, 1], [-26, 0], CLAMP);
  const q3In = reveal(frame, 13, 25);
  const q4In = reveal(frame, 73, 85);

  return (
    <AbsoluteFill data-beat-id={'S4_MID_01'} style={{overflow: 'hidden', background: INK}}>
      <AbsoluteFill style={{transform: `translateX(${track}px)`}}>
        <Img
          src={staticFile('assets/refinery-storage-tanks.jpg')}
          style={{
            position: 'absolute',
            left: -90,
            top: -28,
            width: 2100,
            height: 1136,
            objectFit: 'cover',
            objectPosition: '52% 48%',
          }}
        />
        <AbsoluteFill
          style={{
            background:
              'linear-gradient(180deg, rgba(2,13,16,0.24) 0%, rgba(2,13,16,0.02) 34%, rgba(2,13,16,0.22) 63%, rgba(2,10,10,0.72) 100%)',
          }}
        />
        <TankForecast
          left={185}
          top={378}
          quarter={'Q3 2026'}
          value={'$3.80'}
          opacity={q3In}
          rise={interpolate(q3In, [0, 1], [18, 0])}
        />
        <TankForecast
          left={1180}
          top={430}
          quarter={'Q4 2026'}
          value={'$3.40'}
          opacity={q4In}
          rise={interpolate(q4In, [0, 1], [18, 0])}
        />
      </AbsoluteFill>

      <div
        style={{
          position: 'absolute',
          left: 72,
          top: 62,
          zIndex: 20,
          opacity: headingIn,
          transform: `translateY(${headingY}px)`,
          color: PAPER,
          fontFamily: FONT,
          textShadow: '0 3px 12px rgba(0,0,0,0.72)',
        }}
      >
        <div style={{fontSize: 31, fontWeight: 800, letterSpacing: 4.5}}>U.S. GASOLINE</div>
        <div
          style={{
            display: 'inline-block',
            marginTop: 7,
            padding: '8px 14px 7px',
            background: TEAL,
            color: '#f8fffc',
            fontSize: 24,
            fontWeight: 900,
            letterSpacing: 3.2,
          }}
        >
          FORECAST
        </div>
      </div>

      <Caption
        visible={Boolean(captionsVisible)}
        text={'EIA forecasts gasoline at $3.80 in Q3 and $3.40 in Q4. Both numbers remain forecasts.'}
      />
      <SourceStrip text={'Forecast: U.S. Energy Information Administration, July 7, 2026 | Image: Tony Webster, CC BY 4.0, via Wikimedia Commons; cropped/resized'} />
    </AbsoluteFill>
  );
};

const S4Mid02: React.FC<{captionsVisible?: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const pan = interpolate(frame, [60, 150], [28, -62], CLAMP);
  const priorIn = reveal(frame, 5, 16);
  const priorOut = reveal(frame, 66, 79);
  const priorOpacity = priorIn * (1 - priorOut);
  const importerIn = reveal(frame, 55, 68);
  const producerIn = reveal(frame, 96, 109);
  const importerEmphasis = interpolate(frame, [112, 138], [1, 0.72], CLAMP);

  return (
    <AbsoluteFill data-beat-id={'S4_MID_02'} style={{overflow: 'hidden', background: INK}}>
      <AbsoluteFill style={{transform: `translateX(${pan}px) scale(1.055)`}}>
        <Img
          src={staticFile('assets/commercial-tanker-oil-platform-persian-gulf.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 49%'}}
        />
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(3,16,18,0.16) 0%, rgba(3,16,18,0.03) 32%, rgba(3,12,12,0.3) 64%, rgba(3,10,10,0.8) 100%)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          left: 72,
          top: 58,
          padding: '9px 14px 8px',
          borderLeft: `6px solid ${TEAL}`,
          background: 'rgba(4,14,13,0.82)',
          color: PAPER,
          fontFamily: FONT,
          fontSize: 24,
          fontWeight: 900,
          letterSpacing: 2.3,
        }}
      >
        CONDITIONAL | EFFECTS REQUIRE A SUSTAINED RETREAT
      </div>

      <div
        style={{
          position: 'absolute',
          left: 120,
          right: 120,
          top: 172,
          opacity: priorOpacity,
          transform: `translateY(${interpolate(priorIn, [0, 1], [14, 0])}px)`,
          color: PAPER,
          fontFamily: FONT,
          fontSize: 62,
          fontWeight: 900,
          lineHeight: 1.05,
          letterSpacing: 0.4,
          textAlign: 'center',
          textShadow: '0 4px 15px rgba(0,0,0,0.78)',
        }}
      >
        A DECLINE CAN STILL LEAVE OIL
        <br />
        ABOVE PRIOR-CYCLE AVERAGES
      </div>

      <div
        style={{
          position: 'absolute',
          left: 112,
          top: 603,
          width: 540,
          opacity: importerIn * importerEmphasis,
          transform: `translateX(${pan * 0.55}px) translateY(${interpolate(importerIn, [0, 1], [18, 0])}px)`,
          padding: '18px 22px 20px',
          boxSizing: 'border-box',
          borderLeft: `7px solid ${TEAL}`,
          background: 'rgba(4,14,13,0.82)',
          color: PAPER,
          fontFamily: FONT,
          boxShadow: '0 12px 28px rgba(0,0,0,0.28)',
        }}
      >
        <div style={{fontSize: 23, letterSpacing: 2.3, color: '#9be2d3'}}>LARGE IMPORTERS</div>
        <div style={{marginTop: 4, fontSize: 47, fontWeight: 900}}>POSSIBLE SUPPORT</div>
      </div>

      <div
        style={{
          position: 'absolute',
          right: 118,
          top: 356,
          width: 565,
          opacity: producerIn,
          transform: `translateX(${pan * 0.55}px) translateY(${interpolate(producerIn, [0, 1], [-16, 0])}px)`,
          padding: '18px 22px 20px',
          boxSizing: 'border-box',
          borderRight: `7px solid ${AMBER}`,
          background: 'rgba(4,14,13,0.84)',
          color: PAPER,
          fontFamily: FONT,
          textAlign: 'right',
          boxShadow: '0 12px 28px rgba(0,0,0,0.28)',
        }}
      >
        <div style={{fontSize: 23, letterSpacing: 2.1, color: '#f1cf8e'}}>PRODUCER REVENUE</div>
        <div style={{marginTop: 4, fontSize: 45, fontWeight: 900}}>POSSIBLE PRESSURE</div>
      </div>

      <Caption
        visible={Boolean(captionsVisible)}
        text={'Even if the oil retreat arrives, prices can remain above prior-cycle averages. If sustained, it may support large importers while pressuring producer revenues.'}
      />
      <SourceStrip text={'Analysis: Capital Chronicle | Image: U.S. Navy photo by MC2 Nathan Schaeffer, March 28, 2009'} />
    </AbsoluteFill>
  );
};

const MechanismLabel: React.FC<{
  left: number;
  top: number;
  width: number;
  eyebrow: string;
  lineOne: string;
  lineTwo?: string;
  qualifier: string;
  opacity: number;
  accent?: string;
}> = ({left, top, width, eyebrow, lineOne, lineTwo, qualifier, opacity, accent = TEAL}) => (
  <div
    style={{
      position: 'absolute',
      left,
      top,
      width,
      opacity,
      padding: '15px 17px 17px',
      boxSizing: 'border-box',
      borderLeft: `6px solid ${accent}`,
      background: 'rgba(4,14,13,0.83)',
      color: PAPER,
      fontFamily: FONT,
      boxShadow: '0 12px 26px rgba(0,0,0,0.24)',
    }}
  >
    <div style={{fontSize: 19, fontWeight: 800, letterSpacing: 2.1, color: accent}}>{eyebrow}</div>
    <div style={{marginTop: 5, fontSize: 38, fontWeight: 900, lineHeight: 1.03}}>
      {lineOne}
      {lineTwo ? <><br />{lineTwo}</> : null}
    </div>
    <div style={{marginTop: 8, fontFamily: BODY_FONT, fontSize: 21, fontWeight: 700, letterSpacing: 0.4}}>
      {qualifier}
    </div>
  </div>
);

const S4Mid03: React.FC<{captionsVisible?: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const imageShift = interpolate(frame, [0, 48, 96, 126], [20, 5, -17, -17], CLAMP);
  const stageOne = reveal(frame, 10, 22);
  const stageTwo = reveal(frame, 53, 66);
  const stageThree = reveal(frame, 105, 117);
  const stageOneEmphasis = interpolate(frame, [57, 75], [1, 0.73], CLAMP);
  const stageTwoEmphasis = interpolate(frame, [108, 125], [1, 0.76], CLAMP);

  return (
    <AbsoluteFill data-beat-id={'S4_MID_03'} style={{overflow: 'hidden', background: INK}}>
      <AbsoluteFill style={{transform: `translateX(${imageShift}px) scale(1.045)`}}>
        <Img
          src={staticFile('assets/doe-tanker-terminal-pipeline.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '51% 50%'}}
        />
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(90deg, rgba(3,12,13,0.26) 0%, rgba(3,12,13,0.05) 48%, rgba(3,12,13,0.3) 100%), linear-gradient(180deg, rgba(3,12,13,0.1), rgba(3,12,13,0.64) 100%)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          left: 72,
          top: 58,
          paddingBottom: 9,
          borderBottom: `4px solid ${TEAL}`,
          color: PAPER,
          fontFamily: FONT,
          fontSize: 25,
          fontWeight: 900,
          letterSpacing: 2.4,
          textShadow: '0 3px 10px rgba(0,0,0,0.75)',
        }}
      >
        POTENTIAL TRANSMISSION | CONDITIONS APPLY
      </div>

      <MechanismLabel
        left={104}
        top={212}
        width={470}
        eyebrow={'TERMINAL STAGE'}
        lineOne={'HEADLINE INFLATION'}
        qualifier={'MAY EASE'}
        opacity={stageOne * stageOneEmphasis}
      />
      <MechanismLabel
        left={595}
        top={520}
        width={510}
        eyebrow={'NEAR-TERM CHANNEL'}
        lineOne={'INFLATION'}
        lineTwo={'COMPENSATION'}
        qualifier={'MAY EASE'}
        opacity={stageTwo * stageTwoEmphasis}
      />
      <MechanismLabel
        left={1300}
        top={292}
        width={480}
        eyebrow={'MARKET BOUNDARY'}
        lineOne={'LONG-TERM YIELDS'}
        qualifier={'NO GUARANTEE'}
        opacity={stageThree}
        accent={AMBER}
      />

      <Caption
        visible={Boolean(captionsVisible)}
        text={'Lower gasoline can ease headline inflation and reduce near-term inflation compensation, but lower long-term yields are not guaranteed.'}
      />
      <SourceStrip text={'Analysis: Capital Chronicle | Image: U.S. Department of Energy, Strategic Petroleum Reserve image 011'} />
    </AbsoluteFill>
  );
};

const PolicyCondition: React.FC<{
  top: number;
  index: string;
  text: string;
  opacity: number;
}> = ({top, index, text, opacity}) => (
  <div
    style={{
      position: 'absolute',
      left: 1186,
      right: 68,
      top,
      opacity,
      display: 'flex',
      alignItems: 'center',
      minHeight: 74,
      borderTop: '1px solid rgba(244,241,232,0.3)',
      color: PAPER,
      fontFamily: FONT,
    }}
  >
    <div style={{width: 58, color: TEAL, fontSize: 22, fontWeight: 900, letterSpacing: 2}}>{index}</div>
    <div style={{fontSize: 35, fontWeight: 800, lineHeight: 1.06}}>{text}</div>
  </div>
);

const S4Mid04: React.FC<{captionsVisible?: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const rise = interpolate(frame, [0, 120], [26, -32], CLAMP);
  const policyIn = reveal(frame, 3, 15);
  const conditionOne = reveal(frame, 30, 42);
  const conditionTwo = reveal(frame, 61, 73);
  const conditionThree = reveal(frame, 92, 104);
  const questionIn = reveal(frame, 180, 188);
  const conditionDim = interpolate(questionIn, [0, 1], [1, 0.38], CLAMP);
  const questionTop = captionsVisible ? 720 : 775;

  return (
    <AbsoluteFill data-beat-id={'S4_MID_04'} style={{overflow: 'hidden', background: '#101c1a'}}>
      <div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: '58%', overflow: 'hidden'}}>
        <Img
          src={staticFile('assets/nara-refinery-portrait.jpg')}
          style={{
            position: 'absolute',
            left: -18,
            top: -55,
            width: '108%',
            height: '116%',
            objectFit: 'cover',
            objectPosition: '48% 45%',
            transform: `translateY(${rise}px) scale(1.035)`,
            filter: 'grayscale(1) contrast(1.08)',
          }}
        />
        <AbsoluteFill
          style={{
            background: 'linear-gradient(90deg, rgba(3,10,10,0.04), rgba(3,10,10,0.12) 72%, rgba(3,10,10,0.66))',
          }}
        />
        <div
          style={{
            position: 'absolute',
            left: 58,
            bottom: 108,
            padding: '7px 11px',
            background: 'rgba(4,14,13,0.76)',
            color: MUTED,
            fontFamily: BODY_FONT,
            fontSize: 18,
            fontWeight: 700,
            letterSpacing: 1.2,
          }}
        >
          REFINERY CONTEXT | HISTORICAL IMAGE
        </div>
      </div>

      <div style={{position: 'absolute', left: '58%', right: 0, top: 0, bottom: 0, overflow: 'hidden', background: '#13211f'}}>
        <Img
          src={staticFile('assets/nara-refinery-portrait.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: '66% 46%',
            opacity: 0.13,
            filter: 'grayscale(1) contrast(1.35)',
          }}
        />
        <AbsoluteFill style={{background: 'linear-gradient(135deg, rgba(18,35,32,0.72), rgba(5,15,14,0.96))'}} />
      </div>
      <div style={{position: 'absolute', left: '58%', top: 0, bottom: 0, width: 4, background: TEAL}} />

      <div
        style={{
          position: 'absolute',
          left: 1186,
          right: 68,
          top: 72,
          opacity: policyIn,
          color: PAPER,
          fontFamily: FONT,
        }}
      >
        <div style={{color: TEAL, fontSize: 22, fontWeight: 900, letterSpacing: 2.6}}>
          FEDERAL RESERVE POLICY BOUNDARY
        </div>
        <div style={{marginTop: 13, fontSize: 64, fontWeight: 900, lineHeight: 0.96, letterSpacing: -0.6}}>
          NO AUTOMATIC
          <br />
          FED RESPONSE
        </div>
        <div style={{marginTop: 18, color: MUTED, fontFamily: BODY_FONT, fontSize: 24, fontWeight: 700, lineHeight: 1.22}}>
          Gasoline alone does not determine policy.
        </div>
      </div>

      <PolicyCondition top={360} index={'01'} text={'BROADER PRICE PERSISTENCE'} opacity={conditionOne * conditionDim} />
      <PolicyCondition top={485} index={'02'} text={'LABOR CONDITIONS'} opacity={conditionTwo * conditionDim} />
      <PolicyCondition top={610} index={'03'} text={'INFLATION EXPECTATIONS'} opacity={conditionThree * conditionDim} />

      <div
        style={{
          position: 'absolute',
          left: 1186,
          right: 68,
          top: questionTop,
          opacity: questionIn,
          transform: `translateY(${interpolate(questionIn, [0, 1], [12, 0])}px)`,
          paddingTop: 14,
          borderTop: `5px solid ${AMBER}`,
          color: PAPER,
          fontFamily: FONT,
        }}
      >
        <div style={{color: AMBER, fontSize: 21, fontWeight: 900, letterSpacing: 2.5}}>NEXT</div>
        <div style={{marginTop: 6, fontSize: 36, fontWeight: 900, lineHeight: 1.04}}>
          WHAT CONFIRMS - OR
          <br />
          CHALLENGES - THE PATH?
        </div>
      </div>

      <Caption
        visible={Boolean(captionsVisible)}
        text={'That still does not dictate the Fed. Broader price persistence, labor conditions and inflation expectations matter. What would confirm or challenge the path?'}
      />
      <SourceStrip text={'Policy boundary: Federal Reserve, June 17, 2026; Capital Chronicle | Image: U.S. National Archives / Office of War Information, NARA 535733'} />
    </AbsoluteFill>
  );
};

export const Motion_midform_16x9_S4_BEYOND_THE_BARREL: React.FC<VariantProps> = ({captionsVisible}) => (
  <AbsoluteFill
    data-segment-id={'S4_BEYOND_THE_BARREL'}
    data-duration-frames={735}
    style={{overflow: 'hidden', background: INK}}
  >
    <Sequence from={0} durationInFrames={165}>
      <S4Mid01 captionsVisible={captionsVisible} />
    </Sequence>
    <Sequence from={165} durationInFrames={195}>
      <S4Mid02 captionsVisible={captionsVisible} />
    </Sequence>
    <Sequence from={360} durationInFrames={165}>
      <S4Mid03 captionsVisible={captionsVisible} />
    </Sequence>
    <Sequence from={525} durationInFrames={210}>
      <S4Mid04 captionsVisible={captionsVisible} />
    </Sequence>
  </AbsoluteFill>
);
