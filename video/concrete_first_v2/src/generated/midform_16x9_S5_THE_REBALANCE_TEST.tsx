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

const FACE = 'Bahnschrift Condensed, Arial Narrow, sans-serif';
const BODY = 'Aptos, Segoe UI, sans-serif';
const WHITE = '#f4f1e9';
const MUTED = '#c8ced1';
const TEAL = '#61d6c2';
const TEAL_DARK = '#178777';
const AMBER = '#e7b45d';
const INK = '#071116';
const CLAMP = {
  extrapolateLeft: 'clamp',
  extrapolateRight: 'clamp',
} as const;

const reveal = (frame: number, start: number, length = 6) =>
  interpolate(frame, [start, start + length], [0, 1], CLAMP);

const photoStyle: React.CSSProperties = {
  width: '100%',
  height: '100%',
  objectFit: 'cover',
};

const SourceRail: React.FC<{children: React.ReactNode}> = ({children}) => (
  <div
    style={{
      position: 'absolute',
      zIndex: 30,
      left: 0,
      right: 0,
      bottom: 0,
      height: 116,
      padding: '44px 72px 18px',
      boxSizing: 'border-box',
      background:
        'linear-gradient(180deg, rgba(5,12,16,0), rgba(5,12,16,0.88) 52%, rgba(5,12,16,0.96))',
      color: MUTED,
      fontFamily: BODY,
      fontSize: 24,
      lineHeight: 1.2,
      letterSpacing: 0.15,
      overflow: 'hidden',
      textShadow: '0 1px 3px rgba(0,0,0,0.9)',
    }}
  >
    {children}
  </div>
);

const Caption: React.FC<{show?: boolean; children: React.ReactNode}> = ({
  show,
  children,
}) =>
  show ? (
    <div
      style={{
        position: 'absolute',
        zIndex: 40,
        left: '50%',
        bottom: 122,
        transform: 'translateX(-50%)',
        maxWidth: 1480,
        padding: '10px 18px 11px',
        boxSizing: 'border-box',
        backgroundColor: 'rgba(4,10,13,0.88)',
        borderBottom: `3px solid ${TEAL}`,
        color: WHITE,
        fontFamily: BODY,
        fontSize: 31,
        lineHeight: 1.18,
        textAlign: 'center',
        boxShadow: '0 8px 28px rgba(0,0,0,0.28)',
      }}
    >
      {children}
    </div>
  ) : null;

const WipeLine: React.FC<{
  frame: number;
  at: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
  length?: number;
}> = ({frame, at, children, style, length = 6}) => {
  const progress = reveal(frame, at, length);
  return (
    <div
      style={{
        ...style,
        opacity: progress,
        clipPath: `inset(0 ${(1 - progress) * 100}% 0 0)`,
      }}
    >
      {children}
    </div>
  );
};

const NumberedCondition: React.FC<{
  number: string;
  children: React.ReactNode;
  color?: string;
}> = ({number, children, color = TEAL}) => (
  <div
    style={{
      display: 'grid',
      gridTemplateColumns: '58px 1fr',
      alignItems: 'baseline',
      borderTop: '1px solid rgba(244,241,233,0.34)',
      padding: '14px 0 10px',
    }}
  >
    <span
      style={{
        color,
        fontFamily: FACE,
        fontSize: 28,
        fontWeight: 700,
        letterSpacing: 1,
      }}
    >
      {number}
    </span>
    <span
      style={{
        color: WHITE,
        fontFamily: FACE,
        fontSize: 43,
        fontWeight: 700,
        lineHeight: 1.02,
        letterSpacing: 0.5,
        textTransform: 'uppercase',
        textShadow: '0 2px 8px rgba(0,0,0,0.86)',
      }}
    >
      {children}
    </span>
  </div>
);

const BeatOne: React.FC<{captionsVisible?: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const vesselCallback = frame < 26;

  return (
    <AbsoluteFill data-beat-id='S5-M-01' style={{backgroundColor: INK}}>
      {vesselCallback ? (
        <>
          <Img
            src={staticFile('assets/usns-oiler-strait-of-hormuz.jpg')}
            style={{...photoStyle, objectPosition: 'center 52%'}}
          />
          <AbsoluteFill
            style={{
              background:
                'linear-gradient(180deg, rgba(2,8,12,0.02) 28%, rgba(2,8,12,0.18) 52%, rgba(2,8,12,0.9) 100%)',
            }}
          />
          <div
            style={{
              position: 'absolute',
              zIndex: 5,
              left: 72,
              bottom: 192,
              color: WHITE,
              fontFamily: FACE,
              fontSize: 62,
              fontWeight: 700,
              letterSpacing: 2.2,
              textTransform: 'uppercase',
              textShadow: '0 3px 10px rgba(0,0,0,0.8)',
            }}
          >
            Oil / Strait of Hormuz
          </div>
          <div
            style={{
              position: 'absolute',
              zIndex: 5,
              left: 72,
              bottom: 176,
              width: 540,
              height: 5,
              backgroundColor: TEAL,
            }}
          />
        </>
      ) : (
        <>
          <Img
            src={staticFile('assets/refinery-storage-tanks.jpg')}
            style={{...photoStyle, objectPosition: 'center 52%'}}
          />
          <AbsoluteFill
            style={{
              background:
                'linear-gradient(90deg, rgba(5,13,17,0.91) 0%, rgba(5,13,17,0.72) 37%, rgba(5,13,17,0.32) 68%, rgba(5,13,17,0.52) 100%)',
            }}
          />
          <div
            style={{
              position: 'absolute',
              zIndex: 5,
              left: 72,
              top: 96,
              width: 530,
            }}
          >
            <div
              style={{
                color: TEAL,
                fontFamily: FACE,
                fontSize: 26,
                fontWeight: 700,
                letterSpacing: 3.4,
                textTransform: 'uppercase',
              }}
            >
              Forecast test
            </div>
            <div
              style={{
                marginTop: 16,
                color: WHITE,
                fontFamily: FACE,
                fontSize: 83,
                fontWeight: 700,
                lineHeight: 0.92,
                letterSpacing: -1,
                textTransform: 'uppercase',
                textShadow: '0 3px 12px rgba(0,0,0,0.8)',
              }}
            >
              The rebalance test
            </div>
            <div
              style={{
                marginTop: 30,
                width: 110,
                height: 7,
                backgroundColor: TEAL,
              }}
            />
            <div
              style={{
                marginTop: 26,
                color: MUTED,
                fontFamily: BODY,
                fontSize: 29,
                lineHeight: 1.24,
                maxWidth: 420,
              }}
            >
              Confirmation requires several observations to align.
            </div>
          </div>
          <div
            style={{
              position: 'absolute',
              zIndex: 5,
              left: 690,
              right: 80,
              top: 112,
            }}
          >
            <div
              style={{
                color: WHITE,
                fontFamily: FACE,
                fontSize: 31,
                fontWeight: 700,
                letterSpacing: 3,
                textTransform: 'uppercase',
                marginBottom: 35,
              }}
            >
              Confirmation requires
            </div>
            <WipeLine frame={frame} at={34} length={6}>
              <div
                style={{
                  borderTop: `2px solid ${TEAL}`,
                  padding: '24px 0 31px',
                }}
              >
                <div
                  style={{
                    color: TEAL,
                    fontFamily: FACE,
                    fontSize: 27,
                    fontWeight: 700,
                    letterSpacing: 2.4,
                    textTransform: 'uppercase',
                  }}
                >
                  Traffic
                </div>
                <div
                  style={{
                    marginTop: 8,
                    color: WHITE,
                    fontFamily: FACE,
                    fontSize: 60,
                    fontWeight: 700,
                    lineHeight: 0.98,
                    textTransform: 'uppercase',
                    textShadow: '0 2px 10px rgba(0,0,0,0.85)',
                  }}
                >
                  Continued Hormuz normalization
                </div>
              </div>
            </WipeLine>
            <WipeLine frame={frame} at={68} length={6}>
              <div
                style={{
                  borderTop: '1px solid rgba(244,241,233,0.46)',
                  padding: '24px 0 28px',
                }}
              >
                <div
                  style={{
                    color: TEAL,
                    fontFamily: FACE,
                    fontSize: 27,
                    fontWeight: 700,
                    letterSpacing: 2.4,
                    textTransform: 'uppercase',
                  }}
                >
                  Supply
                </div>
                <div
                  style={{
                    marginTop: 8,
                    color: WHITE,
                    fontFamily: FACE,
                    fontSize: 60,
                    fontWeight: 700,
                    lineHeight: 0.98,
                    textTransform: 'uppercase',
                    textShadow: '0 2px 10px rgba(0,0,0,0.85)',
                  }}
                >
                  Shut-in production restored
                </div>
              </div>
            </WipeLine>
          </div>
        </>
      )}
      <Caption show={captionsVisible}>
        First, Hormuz traffic must keep normalizing, and shut-in production must return.
      </Caption>
      <SourceRail>
        Conditions: governed-article. Vessel: U.S. Navy photo by Mass Communication Specialist 2nd Class Indra Beaufort, Dec. 29, 2020. Tanks: Photo: Tony Webster, CC BY 4.0, via Wikimedia Commons; cropped/resized.
      </SourceRail>
    </AbsoluteFill>
  );
};

const BeatTwo: React.FC<{captionsVisible?: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill data-beat-id='S5-M-02' style={{backgroundColor: INK}}>
      <Img
        src={staticFile('assets/refinery-storage-tanks.jpg')}
        style={{...photoStyle, objectPosition: 'center 52%'}}
      />
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(90deg, rgba(5,13,17,0.82) 0%, rgba(5,13,17,0.58) 57%, rgba(5,13,17,0.84) 100%)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          zIndex: 5,
          left: 72,
          right: 72,
          top: 66,
          display: 'flex',
          alignItems: 'baseline',
          justifyContent: 'space-between',
          borderBottom: '1px solid rgba(244,241,233,0.44)',
          paddingBottom: 20,
        }}
      >
        <div
          style={{
            color: WHITE,
            fontFamily: FACE,
            fontSize: 68,
            fontWeight: 700,
            letterSpacing: 1,
            textTransform: 'uppercase',
          }}
        >
          Confirm if
        </div>
        <div
          style={{
            color: TEAL,
            fontFamily: FACE,
            fontSize: 25,
            fontWeight: 700,
            letterSpacing: 3,
            textTransform: 'uppercase',
          }}
        >
          Rebalance conditions / unresolved
        </div>
      </div>
      <div
        style={{
          position: 'absolute',
          zIndex: 5,
          left: 92,
          top: 198,
          width: 960,
        }}
      >
        <NumberedCondition number='1'>Hormuz traffic normalizes</NumberedCondition>
        <NumberedCondition number='2'>Shut-in production returns</NumberedCondition>
        <WipeLine frame={frame} at={20} length={5}>
          <NumberedCondition number='3'>Inventories build</NumberedCondition>
        </WipeLine>
      </div>
      <WipeLine
        frame={frame}
        at={46}
        length={5}
        style={{
          position: 'absolute',
          zIndex: 5,
          left: 1160,
          right: 78,
          top: 222,
        }}
      >
        <div
          style={{
            borderLeft: `5px solid ${AMBER}`,
            padding: '8px 0 8px 34px',
          }}
        >
          <div
            style={{
              color: AMBER,
              fontFamily: FACE,
              fontSize: 25,
              fontWeight: 700,
              letterSpacing: 3.2,
              textTransform: 'uppercase',
            }}
          >
            Brent / Forecast
          </div>
          <div
            style={{
              marginTop: 25,
              color: WHITE,
              fontFamily: FACE,
              fontSize: 55,
              fontWeight: 700,
              lineHeight: 0.98,
              textTransform: 'uppercase',
              textShadow: '0 2px 10px rgba(0,0,0,0.9)',
            }}
          >
            Trades broadly in line with the EIA path
          </div>
          <div
            style={{
              marginTop: 31,
              color: MUTED,
              fontFamily: BODY,
              fontSize: 25,
              lineHeight: 1.25,
            }}
          >
            A separately labeled forecast benchmark. No shared scale and no observed confirmation.
          </div>
        </div>
      </WipeLine>
      <div
        style={{
          position: 'absolute',
          zIndex: 5,
          left: 92,
          bottom: 148,
          width: 960,
          color: MUTED,
          fontFamily: FACE,
          fontSize: 23,
          fontWeight: 700,
          letterSpacing: 2.2,
          textTransform: 'uppercase',
        }}
      >
        All four conditions remain tests, not completed checks.
      </div>
      <Caption show={captionsVisible}>
        Then inventories need to build, while Brent trades broadly along the EIA's declining forecast path.
      </Caption>
      <SourceRail>
        Conditions: governed-article. Forecast boundary: eia-release-press590. Image credit: Tony Webster, CC BY 4.0, via Wikimedia Commons; cropped/resized.
      </SourceRail>
    </AbsoluteFill>
  );
};

const BeatThree: React.FC<{captionsVisible?: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const portraitReveal = reveal(frame, 0, 4);
  const rows = [
    'Renewed disruption in the strait',
    'Slower field restarts',
    'Persistent inventory draws',
    'Prices materially above forecast',
  ];

  return (
    <AbsoluteFill data-beat-id='S5-M-03' style={{backgroundColor: INK}}>
      <Img
        src={staticFile('assets/refinery-storage-tanks.jpg')}
        style={{
          ...photoStyle,
          position: 'absolute',
          left: '34%',
          width: '66%',
          objectPosition: 'center 52%',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          bottom: 0,
          width: `${34 * portraitReveal}%`,
          overflow: 'hidden',
          borderRight: '2px solid rgba(231,180,93,0.82)',
        }}
      >
        <Img
          src={staticFile('assets/nara-refinery-portrait.jpg')}
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            width: 653,
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center center',
            filter: 'contrast(1.06)',
          }}
        />
        <AbsoluteFill
          style={{
            background:
              'linear-gradient(180deg, rgba(5,11,14,0.08), rgba(5,11,14,0.46) 75%, rgba(5,11,14,0.88))',
          }}
        />
        <div
          style={{
            position: 'absolute',
            left: 52,
            bottom: 154,
            width: 500,
            color: MUTED,
            fontFamily: FACE,
            fontSize: 23,
            fontWeight: 700,
            letterSpacing: 2.4,
            textTransform: 'uppercase',
          }}
        >
          Refinery infrastructure / documentary context
        </div>
      </div>
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(90deg, rgba(5,12,16,0.06) 25%, rgba(5,12,16,0.49) 47%, rgba(5,12,16,0.83) 100%)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          zIndex: 5,
          left: 706,
          right: 72,
          top: 62,
        }}
      >
        <div
          style={{
            color: AMBER,
            fontFamily: FACE,
            fontSize: 70,
            fontWeight: 700,
            letterSpacing: 1.2,
            textTransform: 'uppercase',
          }}
        >
          Challenge if
        </div>
        <div
          style={{
            marginTop: 16,
            color: MUTED,
            fontFamily: BODY,
            fontSize: 25,
            lineHeight: 1.25,
          }}
        >
          These are possible adverse conditions, not depicted events.
        </div>
        <div style={{marginTop: 34}}>
          {rows.map((row, index) => {
            const progress = reveal(frame, 18 + index * 20, 4);
            return (
              <div
                key={row}
                style={{
                  opacity: progress,
                  borderTop:
                    index === 0
                      ? `2px solid ${AMBER}`
                      : '1px solid rgba(244,241,233,0.34)',
                  padding: '18px 0 17px',
                  color: WHITE,
                  fontFamily: FACE,
                  fontSize: 50,
                  fontWeight: 700,
                  lineHeight: 0.98,
                  letterSpacing: 0.2,
                  textTransform: 'uppercase',
                  textShadow: '0 2px 9px rgba(0,0,0,0.9)',
                }}
              >
                {row}
              </div>
            );
          })}
        </div>
      </div>
      <Caption show={captionsVisible}>
        Renewed disruption, slower field restarts, persistent inventory draws, or prices materially above forecast would challenge the rebalance.
      </Caption>
      <SourceRail>
        Conditions: governed-article. Refinery: U.S. National Archives / Office of War Information, NARA 535733. Tanks: Tony Webster, CC BY 4.0, via Wikimedia Commons; cropped/resized.
      </SourceRail>
    </AbsoluteFill>
  );
};

const BeatFour: React.FC<{captionsVisible?: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const divider = reveal(frame, 40, 6);
  const wti = reveal(frame, 10, 5);
  const status = reveal(frame, 18, 5);
  const date = reveal(frame, 26, 5);
  const value = reveal(frame, 34, 5);
  const brent = reveal(frame, 58, 5);

  return (
    <AbsoluteFill data-beat-id='S5-M-04' style={{backgroundColor: INK}}>
      <Img
        src={staticFile('assets/refinery-storage-tanks.jpg')}
        style={{...photoStyle, objectPosition: 'center 52%'}}
      />
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(90deg, rgba(4,11,15,0.85) 0%, rgba(4,11,15,0.67) 48%, rgba(4,11,15,0.79) 52%, rgba(4,11,15,0.88) 100%)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          zIndex: 5,
          left: 72,
          right: 72,
          top: 58,
          color: MUTED,
          fontFamily: FACE,
          fontSize: 24,
          fontWeight: 700,
          letterSpacing: 3.2,
          textTransform: 'uppercase',
        }}
      >
        Benchmark boundary / observation versus forecast
      </div>
      <div
        style={{
          position: 'absolute',
          zIndex: 5,
          left: 102,
          top: 152,
          width: 710,
        }}
      >
        <div
          style={{
            opacity: wti,
            color: WHITE,
            fontFamily: FACE,
            fontSize: 68,
            fontWeight: 700,
            letterSpacing: 1.4,
            textTransform: 'uppercase',
          }}
        >
          WTI
        </div>
        <div
          style={{
            opacity: status,
            marginTop: 6,
            color: TEAL,
            fontFamily: FACE,
            fontSize: 30,
            fontWeight: 700,
            letterSpacing: 3.4,
            textTransform: 'uppercase',
          }}
        >
          Observation
        </div>
        <div
          style={{
            opacity: date,
            marginTop: 52,
            color: MUTED,
            fontFamily: FACE,
            fontSize: 40,
            fontWeight: 700,
            letterSpacing: 1.5,
            textTransform: 'uppercase',
          }}
        >
          Jul 6, 2026
        </div>
        <div
          style={{
            opacity: value,
            marginTop: 2,
            color: WHITE,
            fontFamily: FACE,
            fontSize: 138,
            fontWeight: 700,
            lineHeight: 0.95,
            letterSpacing: -2,
            textShadow: '0 3px 12px rgba(0,0,0,0.85)',
          }}
        >
          $69.60
        </div>
        <div
          style={{
            opacity: value,
            marginTop: 24,
            width: 610,
            height: 7,
            backgroundColor: TEAL_DARK,
          }}
        />
      </div>
      <div
        style={{
          position: 'absolute',
          zIndex: 6,
          left: '50%',
          top: 126,
          bottom: 146,
          width: 2,
          backgroundColor: 'rgba(244,241,233,0.66)',
          transformOrigin: 'top center',
          transform: `scaleY(${divider})`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          zIndex: 7,
          left: '50%',
          top: 412,
          transform: 'translate(-50%, -50%) rotate(-90deg)',
          opacity: divider,
          padding: '7px 15px',
          backgroundColor: 'rgba(5,12,16,0.94)',
          color: MUTED,
          fontFamily: FACE,
          fontSize: 20,
          fontWeight: 700,
          letterSpacing: 2.8,
          textTransform: 'uppercase',
          whiteSpace: 'nowrap',
        }}
      >
        Separate benchmarks
      </div>
      <div
        style={{
          position: 'absolute',
          zIndex: 5,
          left: 1086,
          right: 92,
          top: 162,
          opacity: brent,
        }}
      >
        <div
          style={{
            color: WHITE,
            fontFamily: FACE,
            fontSize: 68,
            fontWeight: 700,
            letterSpacing: 1.4,
            textTransform: 'uppercase',
          }}
        >
          Brent
        </div>
        <div
          style={{
            marginTop: 6,
            color: AMBER,
            fontFamily: FACE,
            fontSize: 30,
            fontWeight: 700,
            letterSpacing: 3.4,
            textTransform: 'uppercase',
          }}
        >
          EIA forecast
        </div>
        <div
          style={{
            marginTop: 88,
            color: WHITE,
            fontFamily: FACE,
            fontSize: 58,
            fontWeight: 700,
            lineHeight: 1,
            letterSpacing: 0.3,
            textTransform: 'uppercase',
            textShadow: '0 2px 10px rgba(0,0,0,0.9)',
          }}
        >
          WTI does not prove this path
        </div>
        <div
          style={{
            marginTop: 34,
            color: MUTED,
            fontFamily: BODY,
            fontSize: 27,
            lineHeight: 1.3,
            maxWidth: 620,
          }}
        >
          Different benchmark. Different evidence status. No common axis or implied price direction.
        </div>
        <div
          style={{
            marginTop: 32,
            width: 240,
            height: 7,
            backgroundColor: AMBER,
          }}
        />
      </div>
      <Caption show={captionsVisible}>
        WTI was $69.60 on July 6. That separate observation does not prove the Brent forecast.
      </Caption>
      <SourceRail>
        WTI observation: fred-dcoilwtico-manifest. Forecast boundary: eia-release-press590. Interpretation boundary: governed-article.
      </SourceRail>
    </AbsoluteFill>
  );
};

const BeatFive: React.FC<{captionsVisible?: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const dates = reveal(frame, 8, 6);
  const confirm = reveal(frame, 36, 6);
  const challenge = reveal(frame, 50, 6);
  const boundary = reveal(frame, 66, 6);
  const oldDivider = interpolate(frame, [0, 15], [1, 0], CLAMP);

  return (
    <AbsoluteFill data-beat-id='S5-M-05' style={{backgroundColor: INK}}>
      <Img
        src={staticFile('assets/refinery-storage-tanks.jpg')}
        style={{...photoStyle, objectPosition: 'center 52%'}}
      />
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(4,11,15,0.56) 0%, rgba(4,11,15,0.43) 36%, rgba(4,11,15,0.82) 75%, rgba(4,11,15,0.94) 100%)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          zIndex: 4,
          left: '50%',
          top: 70,
          bottom: 150,
          width: 2,
          opacity: oldDivider,
          backgroundColor: 'rgba(244,241,233,0.55)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          zIndex: 5,
          left: 72,
          right: 72,
          top: 58,
          opacity: dates,
        }}
      >
        <div
          style={{
            color: TEAL,
            fontFamily: FACE,
            fontSize: 27,
            fontWeight: 700,
            letterSpacing: 3.5,
            textAlign: 'center',
            textTransform: 'uppercase',
          }}
        >
          Checkpoints
        </div>
        <div
          style={{
            marginTop: 21,
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            columnGap: 90,
          }}
        >
          <div
            style={{
              borderTop: `5px solid ${TEAL}`,
              paddingTop: 20,
              color: WHITE,
              fontFamily: FACE,
              fontSize: 76,
              fontWeight: 700,
              letterSpacing: 0.3,
              textAlign: 'right',
              textTransform: 'uppercase',
              textShadow: '0 2px 10px rgba(0,0,0,0.85)',
            }}
          >
            Jul 15, 2026
          </div>
          <div
            style={{
              borderTop: `5px solid ${TEAL}`,
              paddingTop: 20,
              color: WHITE,
              fontFamily: FACE,
              fontSize: 76,
              fontWeight: 700,
              letterSpacing: 0.3,
              textAlign: 'left',
              textTransform: 'uppercase',
              textShadow: '0 2px 10px rgba(0,0,0,0.85)',
            }}
          >
            Aug 11, 2026
          </div>
        </div>
      </div>
      <div
        style={{
          position: 'absolute',
          zIndex: 5,
          left: 106,
          right: 106,
          top: 410,
        }}
      >
        <div
          style={{
            opacity: confirm,
            display: 'grid',
            gridTemplateColumns: '205px 1fr',
            borderTop: '1px solid rgba(244,241,233,0.48)',
            padding: '21px 0 23px',
          }}
        >
          <div
            style={{
              color: TEAL,
              fontFamily: FACE,
              fontSize: 31,
              fontWeight: 700,
              letterSpacing: 2.7,
              textTransform: 'uppercase',
            }}
          >
            Confirm
          </div>
          <div
            style={{
              color: WHITE,
              fontFamily: FACE,
              fontSize: 43,
              fontWeight: 700,
              lineHeight: 1.03,
              textTransform: 'uppercase',
              textShadow: '0 2px 8px rgba(0,0,0,0.86)',
            }}
          >
            Traffic + production + inventory builds + Brent path
          </div>
        </div>
        <div
          style={{
            opacity: challenge,
            display: 'grid',
            gridTemplateColumns: '205px 1fr',
            borderTop: '1px solid rgba(244,241,233,0.48)',
            padding: '21px 0 23px',
          }}
        >
          <div
            style={{
              color: AMBER,
              fontFamily: FACE,
              fontSize: 31,
              fontWeight: 700,
              letterSpacing: 2.7,
              textTransform: 'uppercase',
            }}
          >
            Challenge
          </div>
          <div
            style={{
              color: WHITE,
              fontFamily: FACE,
              fontSize: 41,
              fontWeight: 700,
              lineHeight: 1.03,
              textTransform: 'uppercase',
              textShadow: '0 2px 8px rgba(0,0,0,0.86)',
            }}
          >
            Disruption + slow restarts + draws + materially above-path prices
          </div>
        </div>
        <div
          style={{
            opacity: boundary,
            borderTop: '1px solid rgba(244,241,233,0.48)',
            paddingTop: 27,
            color: WHITE,
            fontFamily: FACE,
            fontSize: 50,
            fontWeight: 700,
            letterSpacing: 3.4,
            textAlign: 'center',
            textTransform: 'uppercase',
          }}
        >
          Forecast, not certainty
        </div>
      </div>
      <Caption show={captionsVisible}>
        July 15 and August 11 are checkpoints. The outcome still depends on those conditions.
      </Caption>
      <SourceRail>
        Checkpoints and forecast boundary: eia-release-press590. Conditions and evidence boundary: governed-article.
      </SourceRail>
    </AbsoluteFill>
  );
};

export const Motion_midform_16x9_S5_THE_REBALANCE_TEST: React.FC<VariantProps> = ({
  captionsVisible,
}) => (
  <AbsoluteFill
    style={{
      backgroundColor: INK,
      color: WHITE,
      overflow: 'hidden',
    }}
  >
    <Sequence from={0} durationInFrames={144}>
      <BeatOne captionsVisible={captionsVisible} />
    </Sequence>
    <Sequence from={144} durationInFrames={150}>
      <BeatTwo captionsVisible={captionsVisible} />
    </Sequence>
    <Sequence from={294} durationInFrames={162}>
      <BeatThree captionsVisible={captionsVisible} />
    </Sequence>
    <Sequence from={456} durationInFrames={168}>
      <BeatFour captionsVisible={captionsVisible} />
    </Sequence>
    <Sequence from={624} durationInFrames={126}>
      <BeatFive captionsVisible={captionsVisible} />
    </Sequence>
  </AbsoluteFill>
);
