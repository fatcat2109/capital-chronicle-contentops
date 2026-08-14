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

const DOCUMENT_FRAMES = 150;
const CHART_FRAMES = 240;
const TOTAL_FRAMES = DOCUMENT_FRAMES + CHART_FRAMES;
const S3_SHORT_01 = 'S3_SHORT_01';
const S3_SHORT_02 = 'S3_SHORT_02';
const DOCUMENT_ASSET = 'assets/eia-release-document-portrait.png';
const CHART_ASSET = 'assets/eia-brent-forecast-portrait.png';

const COLORS = {
  background: '#07131f',
  backgroundDeep: '#030b13',
  paper: '#f1f0e8',
  ink: '#f5f5f0',
  muted: '#aebbc4',
  teal: '#52c9b5',
  amber: '#d9a441',
  rule: 'rgba(211, 223, 228, 0.24)',
} as const;

const FONT = 'Franklin Gothic Medium, Arial Narrow, sans-serif';
const CLAMP = {
  extrapolateLeft: 'clamp' as const,
  extrapolateRight: 'clamp' as const,
};

const SourceLine: React.FC<{text: string}> = ({text}) => (
  <div
    style={{
      position: 'absolute',
      left: 64,
      right: 64,
      bottom: 54,
      zIndex: 12,
      borderTop: `1px solid ${COLORS.rule}`,
      paddingTop: 12,
      color: COLORS.muted,
      fontFamily: FONT,
      fontSize: 28,
      fontWeight: 400,
      lineHeight: '40px',
      letterSpacing: 0.2,
      fontVariantNumeric: 'tabular-nums',
    }}
  >
    {text}
  </div>
);

const Caption: React.FC<{text: string}> = ({text}) => (
  <div
    style={{
      position: 'absolute',
      left: 72,
      right: 72,
      bottom: 310,
      zIndex: 30,
      display: 'flex',
      justifyContent: 'center',
      pointerEvents: 'none',
    }}
  >
    <div
      style={{
        maxWidth: 900,
        boxSizing: 'border-box',
        borderLeft: `5px solid ${COLORS.amber}`,
        backgroundColor: 'rgba(2, 9, 15, 0.9)',
        padding: '16px 22px 17px',
        color: COLORS.ink,
        fontFamily: FONT,
        fontSize: 35,
        fontWeight: 500,
        lineHeight: 1.25,
        letterSpacing: 0.1,
        textAlign: 'left',
      }}
    >
      {text}
    </div>
  </div>
);

const DocumentBeat: React.FC<{captionsVisible: boolean}> = ({
  captionsVisible,
}) => {
  const frame = useCurrentFrame();
  const keylineOpacity = interpolate(frame, [6, 18], [0, 1], CLAMP);
  const keylineTop = interpolate(frame, [36, 60], [408, 742], CLAMP);
  const keylineLeft = interpolate(frame, [36, 60], [206, 183], CLAMP);
  const keylineWidth = interpolate(frame, [36, 60], [420, 714], CLAMP);
  const keylineHeight = interpolate(frame, [36, 60], [78, 300], CLAMP);
  const dateTagOpacity = interpolate(frame, [40, 52], [1, 0], CLAMP);
  const excerptTagOpacity = interpolate(frame, [46, 60], [0, 1], CLAMP);
  const boundaryOpacity = interpolate(frame, [58, 72], [0, 1], CLAMP);

  return (
    <AbsoluteFill
      data-beat-id={S3_SHORT_01}
      style={{
        overflow: 'hidden',
        backgroundColor: COLORS.background,
        backgroundImage:
          'radial-gradient(circle at 82% 18%, rgba(82, 201, 181, 0.08), transparent 30%), linear-gradient(180deg, #081827 0%, #06111b 100%)',
        color: COLORS.ink,
        fontFamily: FONT,
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: 48,
          left: 64,
          right: 64,
          zIndex: 8,
          display: 'flex',
          justifyContent: 'space-between',
          color: COLORS.amber,
          fontSize: 22,
          fontWeight: 700,
          letterSpacing: 2.4,
          lineHeight: 1,
        }}
      >
        <span>THE FORECAST ON RECORD</span>
        <span>OFFICIAL EIA RELEASE</span>
      </div>

      <div
        style={{
          position: 'absolute',
          top: 91,
          left: 64,
          right: 64,
          zIndex: 8,
          fontSize: 56,
          fontWeight: 700,
          lineHeight: 1,
          letterSpacing: 0.8,
        }}
      >
        BRENT OIL FORECAST
      </div>

      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 64,
          right: 64,
          zIndex: 8,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderTop: `1px solid ${COLORS.rule}`,
          paddingTop: 13,
          color: COLORS.muted,
          fontSize: 24,
          lineHeight: 1,
          letterSpacing: 0.8,
        }}
      >
        <span>U.S. ENERGY INFORMATION ADMINISTRATION</span>
        <span style={{color: COLORS.ink, fontVariantNumeric: 'tabular-nums'}}>
          JULY 7, 2026
        </span>
      </div>

      <div
        style={{
          position: 'absolute',
          left: '4%',
          top: '14%',
          width: '92%',
          height: '67%',
          zIndex: 1,
          overflow: 'hidden',
          boxSizing: 'border-box',
          border: '1px solid rgba(241, 240, 232, 0.24)',
          backgroundColor: COLORS.paper,
          boxShadow: '0 24px 70px rgba(0, 0, 0, 0.28)',
        }}
      >
        <Img
          alt='Official EIA release dated July 7, 2026'
          src={staticFile(DOCUMENT_ASSET)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'contain',
            objectPosition: 'center center',
          }}
        />
      </div>

      <div
        style={{
          position: 'absolute',
          zIndex: 5,
          top: keylineTop,
          left: keylineLeft,
          width: keylineWidth,
          height: keylineHeight,
          boxSizing: 'border-box',
          border: `3px solid ${COLORS.amber}`,
          backgroundColor: 'rgba(217, 164, 65, 0.08)',
          boxShadow: '0 0 0 1px rgba(4, 12, 18, 0.35)',
          opacity: keylineOpacity,
        }}
      >
        <div
          style={{
            position: 'absolute',
            left: -3,
            top: -42,
            padding: '7px 12px 6px',
            backgroundColor: COLORS.amber,
            color: '#101315',
            fontSize: 21,
            fontWeight: 700,
            lineHeight: 1,
            letterSpacing: 1.2,
            whiteSpace: 'nowrap',
            opacity: dateTagOpacity,
          }}
        >
          SOURCE DATE / JULY 7, 2026
        </div>
        <div
          style={{
            position: 'absolute',
            left: -3,
            top: 225 - keylineTop,
            padding: '7px 12px 6px',
            backgroundColor: COLORS.amber,
            color: '#101315',
            fontSize: 21,
            fontWeight: 700,
            lineHeight: 1,
            letterSpacing: 1.2,
            whiteSpace: 'nowrap',
            opacity: excerptTagOpacity,
          }}
        >
          FORECAST EXCERPT / YEAR-END
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          left: 64,
          right: 64,
          top: 1580,
          zIndex: 10,
          opacity: boundaryOpacity,
        }}
      >
        <div
          style={{
            marginBottom: 10,
            color: COLORS.amber,
            fontSize: 20,
            fontWeight: 700,
            lineHeight: 1,
            letterSpacing: 2.2,
          }}
        >
          YEAR-END COMPARISON
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 18,
            borderTop: `1px solid ${COLORS.rule}`,
            paddingTop: 12,
          }}
        >
          <span
            style={{
              color: COLORS.ink,
              fontSize: 31,
              fontWeight: 700,
              lineHeight: 1.08,
              letterSpacing: 0.5,
            }}
          >
            NEAR PRE-CONFLICT LEVELS BY YEAR-END
          </span>
          <span
            style={{
              flex: '0 0 auto',
              border: `2px solid ${COLORS.amber}`,
              padding: '7px 11px 6px',
              color: COLORS.amber,
              fontSize: 20,
              fontWeight: 700,
              lineHeight: 1,
              letterSpacing: 1.5,
            }}
          >
            FORECAST
          </span>
        </div>
      </div>

      <SourceLine text='Source: U.S. Energy Information Administration, July 7, 2026.' />

      {captionsVisible ? (
        <Caption
          text={`This is EIA's July 7, 2026 release. Its forward numbers are forecasts, not outcomes.`}
        />
      ) : null}
    </AbsoluteFill>
  );
};

const ChartKeyline: React.FC<{
  left: number;
  top: number;
  width: number;
  height: number;
  label: string;
  status: string;
  opacity: number;
  color: string;
}> = ({left, top, width, height, label, status, opacity, color}) => (
  <div
    style={{
      position: 'absolute',
      zIndex: 6,
      left,
      top,
      width,
      height,
      boxSizing: 'border-box',
      border: `3px solid ${color}`,
      backgroundColor: 'rgba(4, 12, 19, 0.04)',
      boxShadow: '0 0 0 1px rgba(2, 7, 12, 0.45)',
      opacity,
    }}
  >
    <div
      style={{
        position: 'absolute',
        top: -43,
        left: -3,
        display: 'flex',
        alignItems: 'center',
        gap: 9,
        padding: '7px 11px 6px',
        backgroundColor: COLORS.backgroundDeep,
        border: `2px solid ${color}`,
        color: COLORS.ink,
        fontSize: 21,
        fontWeight: 700,
        lineHeight: 1,
        letterSpacing: 0.6,
        whiteSpace: 'nowrap',
      }}
    >
      <span>{label}</span>
      <span style={{color}}>/ {status}</span>
    </div>
  </div>
);

const ChartBeat: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const juneIn = interpolate(frame, [4, 22], [0, 1], CLAMP);
  const juneDim = interpolate(frame, [156, 182], [1, 0.45], CLAMP);
  const q3Opacity = interpolate(frame, [34, 60], [0, 1], CLAMP);
  const year2027Opacity = interpolate(frame, [82, 110], [0, 1], CLAMP);
  const questionOpacity = interpolate(frame, [174, 196], [0, 1], CLAMP);
  const boundaryOpacity = interpolate(frame, [144, 174], [0, 1], CLAMP);

  return (
    <AbsoluteFill
      data-beat-id={S3_SHORT_02}
      style={{
        overflow: 'hidden',
        backgroundColor: COLORS.backgroundDeep,
        backgroundImage:
          'radial-gradient(circle at 18% 20%, rgba(82, 201, 181, 0.08), transparent 29%), linear-gradient(180deg, #07131f 0%, #030b13 100%)',
        color: COLORS.ink,
        fontFamily: FONT,
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: 48,
          left: 64,
          right: 64,
          zIndex: 9,
          display: 'flex',
          justifyContent: 'space-between',
          color: COLORS.amber,
          fontSize: 22,
          fontWeight: 700,
          letterSpacing: 2.3,
          lineHeight: 1,
        }}
      >
        <span>BRENT OIL FORECAST</span>
        <span>EIA JULY 2026 STEO</span>
      </div>

      <div
        style={{
          position: 'absolute',
          top: 91,
          left: 64,
          right: 64,
          zIndex: 9,
          fontSize: 54,
          fontWeight: 700,
          lineHeight: 1,
          letterSpacing: 0.6,
        }}
      >
        REFERENCE VS. FORECAST
      </div>

      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 64,
          right: 64,
          zIndex: 9,
          display: 'flex',
          justifyContent: 'space-between',
          borderTop: `1px solid ${COLORS.rule}`,
          paddingTop: 13,
          color: COLORS.muted,
          fontSize: 24,
          fontWeight: 700,
          lineHeight: 1,
          letterSpacing: 0.8,
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        <span>JUNE $85 / REFERENCE</span>
        <span style={{color: COLORS.amber}}>
          Q3 $74 / 2027 $65 / FORECAST
        </span>
      </div>

      <div
        style={{
          position: 'absolute',
          left: '3%',
          top: '14%',
          width: '94%',
          height: '66%',
          zIndex: 1,
          overflow: 'hidden',
          boxSizing: 'border-box',
          border: '1px solid rgba(211, 223, 228, 0.18)',
          backgroundColor: '#030b13',
          boxShadow: '0 24px 70px rgba(0, 0, 0, 0.3)',
        }}
      >
        <Img
          alt='Native Brent forecast comparison with June, Q3, and 2027 labels'
          src={staticFile(CHART_ASSET)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'contain',
            objectPosition: 'center center',
          }}
        />
      </div>

      <ChartKeyline
        left={190}
        top={445}
        width={270}
        height={135}
        label='JUNE $85'
        status='REFERENCE'
        opacity={juneIn * juneDim}
        color={COLORS.paper}
      />
      <ChartKeyline
        left={408}
        top={758}
        width={266}
        height={148}
        label='Q3 $74'
        status='FORECAST'
        opacity={q3Opacity}
        color={COLORS.amber}
      />
      <ChartKeyline
        left={684}
        top={1080}
        width={230}
        height={154}
        label='2027 $65'
        status='FORECAST'
        opacity={year2027Opacity}
        color={COLORS.amber}
      />

      <div
        style={{
          position: 'absolute',
          left: 64,
          right: 64,
          top: 1583,
          zIndex: 12,
          opacity: questionOpacity,
          borderTop: `2px solid ${COLORS.amber}`,
          paddingTop: 12,
        }}
      >
        <div
          style={{
            marginBottom: 9,
            color: COLORS.amber,
            fontSize: 20,
            fontWeight: 700,
            lineHeight: 1,
            letterSpacing: 2.1,
            opacity: boundaryOpacity,
          }}
        >
          FORECAST, NOT CERTAINTY / IF THIS PATH HOLDS
        </div>
        <div
          style={{
            color: COLORS.ink,
            fontSize: 43,
            fontWeight: 700,
            lineHeight: 1.05,
            letterSpacing: 0.5,
            whiteSpace: 'nowrap',
          }}
        >
          WHAT WOULD THIS PATH CHANGE?
        </div>
      </div>

      <SourceLine text='Data: U.S. EIA July 2026 STEO; release: July 7, 2026; chart: Capital Chronicle.' />

      {captionsVisible ? (
        <Caption
          text={`From June's $85 reference, EIA forecasts $74 in Q3 and $65 in 2027 - and a return near pre-conflict levels by year-end.`}
        />
      ) : null}
    </AbsoluteFill>
  );
};

export const Motion_short_9x16_S3_THE_FORECAST_ON_RECORD: React.FC<
  VariantProps
> = ({captionsVisible}) => (
  <AbsoluteFill
    data-duration-frames={TOTAL_FRAMES}
    style={{backgroundColor: COLORS.backgroundDeep}}
  >
    <Sequence from={0} durationInFrames={DOCUMENT_FRAMES}>
      <DocumentBeat captionsVisible={Boolean(captionsVisible)} />
    </Sequence>
    <Sequence from={DOCUMENT_FRAMES} durationInFrames={CHART_FRAMES}>
      <ChartBeat captionsVisible={Boolean(captionsVisible)} />
    </Sequence>
  </AbsoluteFill>
);
