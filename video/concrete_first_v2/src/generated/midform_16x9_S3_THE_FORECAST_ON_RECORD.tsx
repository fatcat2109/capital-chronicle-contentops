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
import type {VariantProps} from '../types';

const COLORS = {
  ink: '#06111d',
  navy: '#082b3d',
  paper: '#f2f1eb',
  white: '#f7f8f6',
  muted: '#bdc9d2',
  teal: '#3dc5b4',
  amber: '#e5a945',
};

const DOCUMENT_ASSET = staticFile('assets/eia-release-document-landscape.png');
const CHART_ASSET = staticFile('assets/eia-brent-forecast-landscape.png');

const fadeIn = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, end], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

const SourceLine: React.FC<{children: React.ReactNode}> = ({children}) => (
  <div
    style={{
      position: 'absolute',
      zIndex: 12,
      left: 92,
      right: 92,
      bottom: 22,
      minHeight: 42,
      display: 'flex',
      alignItems: 'center',
      padding: '4px 12px 5px',
      color: COLORS.muted,
      background:
        'linear-gradient(90deg, rgba(4,14,23,0.9) 0%, rgba(4,14,23,0.7) 72%, rgba(4,14,23,0) 100%)',
      fontFamily: 'Trebuchet MS, Verdana, sans-serif',
      fontSize: 30,
      lineHeight: 1.2,
      letterSpacing: 0.15,
      whiteSpace: 'nowrap',
      textShadow: '0 2px 5px rgba(0,0,0,0.8)',
    }}
  >
    {children}
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
        zIndex: 14,
        left: 285,
        right: 285,
        bottom: 120,
        padding: '14px 22px 15px',
        color: COLORS.white,
        backgroundColor: 'rgba(4,14,23,0.91)',
        borderLeft: `5px solid ${COLORS.amber}`,
        fontFamily: 'Trebuchet MS, Verdana, sans-serif',
        fontSize: 38,
        fontWeight: 700,
        lineHeight: 1.22,
        textAlign: 'center',
        boxShadow: '0 8px 28px rgba(0,0,0,0.28)',
      }}
    >
      {text}
    </div>
  );
};

const KeyTag: React.FC<{
  children: React.ReactNode;
  tone: 'reference' | 'forecast' | 'source';
  opacity?: number;
}> = ({children, tone, opacity = 1}) => {
  const color =
    tone === 'forecast'
      ? COLORS.amber
      : tone === 'reference'
        ? COLORS.white
        : COLORS.teal;

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        minHeight: 44,
        padding: '7px 13px 6px',
        color,
        backgroundColor: 'rgba(4,14,23,0.78)',
        borderLeft: `5px solid ${color}`,
        borderTop: `1px solid ${color}88`,
        borderBottom: `1px solid ${color}88`,
        opacity,
        fontFamily: 'Trebuchet MS, Verdana, sans-serif',
        fontSize: 25,
        fontWeight: 800,
        lineHeight: 1.05,
        letterSpacing: 1.1,
        textTransform: 'uppercase',
        whiteSpace: 'nowrap',
        textShadow: '0 2px 4px rgba(0,0,0,0.8)',
      }}
    >
      {children}
    </div>
  );
};

const DocumentBug: React.FC<{secondary: string}> = ({secondary}) => (
  <div
    style={{
      position: 'absolute',
      zIndex: 5,
      top: 34,
      right: 72,
      width: 350,
      padding: '10px 14px 11px 16px',
      color: COLORS.white,
      backgroundColor: 'rgba(4,25,38,0.9)',
      borderLeft: `5px solid ${COLORS.amber}`,
      fontFamily: 'Trebuchet MS, Verdana, sans-serif',
      textTransform: 'uppercase',
      textAlign: 'right',
    }}
  >
    <div style={{fontSize: 27, fontWeight: 800, letterSpacing: 1.1}}>
      Brent oil forecast
    </div>
    <div
      style={{
        marginTop: 4,
        color: COLORS.muted,
        fontSize: 19,
        fontWeight: 700,
        letterSpacing: 1.5,
      }}
    >
      {secondary}
    </div>
  </div>
);

const S3Mid01: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const dateOpacity = fadeIn(frame, fps, fps * 1.5);

  return (
    <AbsoluteFill
      data-beat-id='S3_MID_01'
      style={{backgroundColor: COLORS.paper, overflow: 'hidden'}}
    >
      <Img
        src={DOCUMENT_ASSET}
        alt=''
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: 'center center',
        }}
      />

      <DocumentBug secondary='Official EIA release' />

      <div
        style={{
          position: 'absolute',
          zIndex: 6,
          left: 139,
          top: 126,
          width: 292,
          height: 62,
          borderBottom: `5px solid ${COLORS.amber}`,
          borderLeft: `2px solid ${COLORS.amber}`,
          opacity: dateOpacity,
          boxShadow: '0 7px 0 rgba(229,169,69,0.14)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          zIndex: 6,
          left: 453,
          top: 139,
          color: COLORS.navy,
          opacity: dateOpacity,
          fontFamily: 'Trebuchet MS, Verdana, sans-serif',
          fontSize: 25,
          fontWeight: 800,
          letterSpacing: 1.1,
          textTransform: 'uppercase',
        }}
      >
        Release date / July 7, 2026
      </div>

      <Caption
        visible={captionsVisible}
        text={`This is the source on record: EIA's July 7, 2026 release, before any broader interpretation.`}
      />
      <SourceLine>
        Source: U.S. Energy Information Administration, July 7, 2026.
      </SourceLine>
    </AbsoluteFill>
  );
};

const S3Mid02: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const highlightOpacity = fadeIn(frame, fps * 0.5, fps * 1.2);
  const boundaryOpacity = fadeIn(frame, fps * 1.2, fps * 2);

  return (
    <AbsoluteFill
      data-beat-id='S3_MID_02'
      style={{backgroundColor: COLORS.paper, overflow: 'hidden'}}
    >
      <Img
        src={DOCUMENT_ASSET}
        alt=''
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: 'center center',
          transform: 'scale(1.08) translateY(-1.2%)',
          transformOrigin: '50% 40%',
        }}
      />

      <DocumentBug secondary='July 7, 2026 / forecast language' />

      <div
        style={{
          position: 'absolute',
          zIndex: 5,
          left: 142,
          right: 142,
          top: 604,
          height: 151,
          backgroundColor: 'rgba(229,169,69,0.12)',
          border: `3px solid ${COLORS.amber}`,
          boxShadow:
            'inset 0 0 0 2px rgba(255,255,255,0.12), 0 5px 20px rgba(0,0,0,0.12)',
          opacity: highlightOpacity,
        }}
      >
        <div
          style={{
            position: 'absolute',
            left: 'auto',
            right: -70,
            top: -474,
            height: 40,
            display: 'flex',
            alignItems: 'center',
            padding: '0 13px',
            color: COLORS.ink,
            backgroundColor: COLORS.amber,
            fontFamily: 'Trebuchet MS, Verdana, sans-serif',
            fontSize: 22,
            fontWeight: 800,
            letterSpacing: 1.5,
            textTransform: 'uppercase',
            whiteSpace: 'nowrap',
          }}
        >
          Year-end comparison / forecast language
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          zIndex: 7,
          left: 144,
          top: 777,
        }}
      >
        <KeyTag tone='forecast' opacity={boundaryOpacity}>
          Forecast, not result
        </KeyTag>
      </div>

      <Caption
        visible={captionsVisible}
        text='EIA forecasts prices near pre-conflict levels by year-end. That is a projection, not a reported result.'
      />
      <SourceLine>
        Source: U.S. Energy Information Administration, July 7, 2026.
      </SourceLine>
    </AbsoluteFill>
  );
};

const ChartHeader: React.FC<{detail?: boolean}> = ({detail = false}) => (
  <div
    style={{
      position: 'absolute',
      zIndex: 7,
      top: 34,
      right: 72,
      width: 455,
      padding: '10px 0 11px 18px',
      color: COLORS.white,
      background:
        'linear-gradient(90deg, rgba(4,14,23,0.94) 0%, rgba(4,14,23,0.72) 78%, rgba(4,14,23,0) 100%)',
      borderLeft: `5px solid ${COLORS.teal}`,
      fontFamily: 'Trebuchet MS, Verdana, sans-serif',
      textTransform: 'uppercase',
    }}
  >
    <div style={{fontSize: 27, fontWeight: 800, letterSpacing: 1.2}}>
      Brent oil forecast
    </div>
    <div
      style={{
        marginTop: 3,
        color: COLORS.muted,
        fontSize: 19,
        fontWeight: 700,
        letterSpacing: 1.4,
      }}
    >
      {detail ? 'Forward values / status detail' : 'June reference / forward values'}
    </div>
  </div>
);

const S3Mid03: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const juneOpacity = fadeIn(frame, fps * 0.8, fps * 1.4);

  return (
    <AbsoluteFill
      data-beat-id='S3_MID_03'
      style={{backgroundColor: COLORS.ink, overflow: 'hidden'}}
    >
      <Img
        src={CHART_ASSET}
        alt=''
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: 'center center',
        }}
      />

      <ChartHeader />

      <div
        style={{
          position: 'absolute',
          zIndex: 6,
          left: 154,
          top: 122,
          width: 77,
          height: 77,
          border: `3px solid ${COLORS.white}`,
          opacity: juneOpacity,
          boxShadow: '0 0 0 8px rgba(247,248,246,0.08)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          zIndex: 7,
          left: 255,
          top: 183,
        }}
      >
        <KeyTag tone='reference' opacity={juneOpacity}>
          June / $85 / reference
        </KeyTag>
      </div>

      <div
        style={{
          position: 'absolute',
          zIndex: 7,
          left: 812,
          top: 548,
        }}
      >
        <KeyTag tone='forecast'>Q3 / $74 / forecast</KeyTag>
      </div>
      <div
        style={{
          position: 'absolute',
          zIndex: 7,
          right: 92,
          top: 730,
        }}
      >
        <KeyTag tone='forecast'>2027 / $65 / forecast</KeyTag>
      </div>

      <Caption
        visible={captionsVisible}
        text='The comparison begins with June Brent at $85 - a reference point, not one of the forward values.'
      />
      <SourceLine>
        Data: U.S. EIA July 2026 STEO; release: July 7, 2026; chart: Capital Chronicle.
      </SourceLine>
    </AbsoluteFill>
  );
};

const S3Mid04: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const q3Opacity = fadeIn(frame, fps * 0.5, fps * 1.05);
  const yearOpacity = fadeIn(frame, fps * 1.65, fps * 2.2);
  const boundaryOpacity = fadeIn(frame, fps * 4.8, fps * 5.35);
  const questionOpacity = fadeIn(frame, fps * 6.5, fps * 7.05);

  return (
    <AbsoluteFill
      data-beat-id='S3_MID_04'
      style={{backgroundColor: COLORS.ink, overflow: 'hidden'}}
    >
      <Img
        src={CHART_ASSET}
        alt=''
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          objectPosition: 'center center',
        }}
      />

      <ChartHeader detail />

      <div
        style={{
          position: 'absolute',
          zIndex: 6,
          left: 32,
          top: 177,
          opacity: 0.34,
        }}
      >
        <KeyTag tone='reference'>June / $85 / reference</KeyTag>
      </div>

      <div
        style={{
          position: 'absolute',
          zIndex: 7,
          left: 742,
          top: 492,
        }}
      >
        <KeyTag tone='forecast' opacity={q3Opacity}>
          Q3 / $74 / forecast
        </KeyTag>
      </div>
      <div
        style={{
          position: 'absolute',
          zIndex: 7,
          right: 76,
          top: 716,
        }}
      >
        <KeyTag tone='forecast' opacity={yearOpacity}>
          2027 / $65 / forecast
        </KeyTag>
      </div>

      <div
        style={{
          position: 'absolute',
          zIndex: 8,
          top: 143,
          right: 74,
          opacity: boundaryOpacity,
        }}
      >
        <KeyTag tone='forecast'>Forecast, not certainty</KeyTag>
      </div>

      <div
        style={{
          position: 'absolute',
          zIndex: 8,
          top: 232,
          right: 76,
          width: 610,
          paddingTop: 15,
          color: COLORS.white,
          borderTop: `5px solid ${COLORS.amber}`,
          opacity: questionOpacity,
          fontFamily: 'Trebuchet MS, Verdana, sans-serif',
          fontSize: 54,
          fontWeight: 800,
          lineHeight: 1.05,
          letterSpacing: 0.5,
          textAlign: 'right',
          textTransform: 'uppercase',
          textShadow: '0 4px 12px rgba(0,0,0,0.9)',
        }}
      >
        If this path holds,
        <br />
        what changes?
      </div>

      <Caption
        visible={captionsVisible}
        text='The forward values are $74 in the third quarter and $65 in 2027. Both are forecasts, not certainties.'
      />
      <SourceLine>
        Data: U.S. EIA July 2026 STEO; release: July 7, 2026; chart: Capital Chronicle.
      </SourceLine>
    </AbsoluteFill>
  );
};

export const Motion_midform_16x9_S3_THE_FORECAST_ON_RECORD: React.FC<
  VariantProps
> = ({captionsVisible}) => {
  return (
    <AbsoluteFill style={{backgroundColor: COLORS.ink}}>
      <Sequence from={0} durationInFrames={195}>
        <S3Mid01 captionsVisible={captionsVisible} />
      </Sequence>
      <Sequence from={195} durationInFrames={165}>
        <S3Mid02 captionsVisible={captionsVisible} />
      </Sequence>
      <Sequence from={360} durationInFrames={225}>
        <S3Mid03 captionsVisible={captionsVisible} />
      </Sequence>
      <Sequence from={585} durationInFrames={225}>
        <S3Mid04 captionsVisible={captionsVisible} />
      </Sequence>
    </AbsoluteFill>
  );
};
