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

const DISPLAY_FONT = 'Franklin Gothic Medium, Aptos Display, sans-serif';
const TEXT_FONT = 'Aptos, Trebuchet MS, sans-serif';

const COLORS = {
  ink: '#071018',
  white: '#f4f3ed',
  muted: '#cbd2d3',
  confirm: '#55d2c0',
  challenge: '#e6aa42',
};

const BEAT_1_FRAMES = 114;
const BEAT_2_FRAMES = 111;
const BEAT_3_FRAMES = 135;

const reveal = (frame: number, start: number, length = 4) =>
  interpolate(frame, [start, start + length], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

const DocumentaryPlate: React.FC<{
  asset: string;
  objectPosition: string;
  darkness?: number;
}> = ({asset, objectPosition, darkness = 0.18}) => (
  <AbsoluteFill>
    <Img
      alt=''
      src={staticFile(asset)}
      style={{
        width: '100%',
        height: '100%',
        objectFit: 'cover',
        objectPosition,
      }}
    />
    <AbsoluteFill style={{backgroundColor: `rgba(2, 8, 14, ${darkness})`}} />
  </AbsoluteFill>
);

const SourceRail: React.FC<{lines: string[]}> = ({lines}) => (
  <div
    style={{
      position: 'absolute',
      left: 64,
      right: 64,
      bottom: 42,
      zIndex: 30,
      borderTop: '2px solid rgba(244, 243, 237, 0.38)',
      paddingTop: 14,
      color: COLORS.muted,
      fontFamily: TEXT_FONT,
      fontSize: 32,
      lineHeight: 1.2,
      letterSpacing: 0.1,
      overflowWrap: 'anywhere',
      textShadow: '0 2px 12px rgba(0, 0, 0, 0.9)',
    }}
  >
    {lines.map((line, index) => (
      <div key={`${index}-${line}`}>{line}</div>
    ))}
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
        left: 64,
        right: 64,
        bottom: 250,
        zIndex: 40,
        padding: '12px 18px 14px',
        backgroundColor: 'rgba(3, 10, 16, 0.88)',
        borderLeft: `5px solid ${COLORS.white}`,
        color: COLORS.white,
        fontFamily: TEXT_FONT,
        fontSize: 34,
        fontWeight: 700,
        lineHeight: 1.2,
      }}
    >
      {text}
    </div>
  );
};

const Eyebrow: React.FC<{text: string}> = ({text}) => (
  <div
    style={{
      position: 'absolute',
      top: 92,
      left: 64,
      right: 64,
      zIndex: 10,
      color: COLORS.white,
      fontFamily: TEXT_FONT,
      fontSize: 32,
      fontWeight: 800,
      letterSpacing: 3.8,
      textTransform: 'uppercase',
      textShadow: '0 3px 15px rgba(0, 0, 0, 0.92)',
    }}
  >
    {text}
  </div>
);

const ConditionRow: React.FC<{
  top: number;
  label: string;
  detail: string;
  accent: string;
  opacity: number;
  forecast?: boolean;
}> = ({top, label, detail, accent, opacity, forecast = false}) => (
  <div
    style={{
      position: 'absolute',
      top,
      left: 64,
      right: 64,
      zIndex: 12,
      opacity,
      borderTop: `2px solid ${accent}`,
      paddingTop: 13,
      textShadow: '0 3px 18px rgba(0, 0, 0, 0.96)',
    }}
  >
    <div
      style={{
        color: accent,
        fontFamily: TEXT_FONT,
        fontSize: 29,
        fontWeight: 800,
        letterSpacing: 3.2,
        lineHeight: 1,
        textTransform: 'uppercase',
      }}
    >
      {label}
    </div>
    <div
      style={{
        marginTop: 7,
        color: COLORS.white,
        fontFamily: DISPLAY_FONT,
        fontSize: label === 'BRENT' ? 55 : 64,
        fontWeight: 900,
        letterSpacing: 0.4,
        lineHeight: 0.98,
        textTransform: 'uppercase',
      }}
    >
      {detail}
    </div>
    {forecast ? (
      <div
        style={{
          marginTop: 10,
          color: COLORS.muted,
          fontFamily: TEXT_FONT,
          fontSize: 25,
          fontWeight: 800,
          letterSpacing: 3,
          textTransform: 'uppercase',
        }}
      >
        EIA path / forecast
      </div>
    ) : null}
  </div>
);

const ConfirmBeat: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const tankPhase = frame >= 24;

  return (
    <AbsoluteFill data-beat-id={'S5-S-01'} style={{backgroundColor: COLORS.ink}}>
      <DocumentaryPlate
        asset={
          tankPhase
            ? 'assets/refinery-storage-tanks.jpg'
            : 'assets/usns-oiler-strait-of-hormuz.jpg'
        }
        objectPosition={tankPhase ? '52% 50%' : '43% 50%'}
        darkness={tankPhase ? 0.2 : 0.12}
      />
      <AbsoluteFill
        style={{
          background: tankPhase
            ? 'linear-gradient(180deg, rgba(3, 10, 17, 0.12) 0%, rgba(3, 10, 17, 0.5) 23%, rgba(3, 10, 17, 0.84) 52%, rgba(3, 10, 17, 0.72) 100%)'
            : 'linear-gradient(180deg, rgba(3, 10, 17, 0.04) 0%, rgba(3, 10, 17, 0.08) 38%, rgba(3, 10, 17, 0.86) 68%, rgba(3, 10, 17, 0.86) 100%)',
        }}
      />

      <Eyebrow text='Oil / Strait of Hormuz' />

      {tankPhase ? (
        <>
          <div
            style={{
              position: 'absolute',
              top: 255,
              left: 64,
              right: 64,
              zIndex: 12,
              opacity: reveal(frame, 24, 4),
              color: COLORS.confirm,
              fontFamily: DISPLAY_FONT,
              fontSize: 112,
              fontWeight: 900,
              letterSpacing: -1.5,
              lineHeight: 0.92,
              textTransform: 'uppercase',
              textShadow: '0 4px 24px rgba(0, 0, 0, 0.95)',
            }}
          >
            Confirm if
          </div>

          <ConditionRow
            top={500}
            label='Hormuz traffic'
            detail='Normalizes'
            accent={COLORS.confirm}
            opacity={reveal(frame, 31, 4)}
          />
          <ConditionRow
            top={688}
            label='Production'
            detail='Is restored'
            accent={COLORS.confirm}
            opacity={reveal(frame, 46, 4)}
          />
          <ConditionRow
            top={876}
            label='Inventories'
            detail='Build'
            accent={COLORS.confirm}
            opacity={reveal(frame, 61, 4)}
          />
          <ConditionRow
            top={1064}
            label='Brent'
            detail='Stays broadly near the EIA path'
            accent={COLORS.confirm}
            opacity={reveal(frame, 76, 4)}
            forecast
          />
        </>
      ) : null}

      <Caption
        visible={captionsVisible}
        text='Confirmation requires Hormuz traffic, production, inventories, and Brent to align.'
      />
      <SourceRail
        lines={[
          'Conditions: governed-article.',
          'Vessel: U.S. Navy photo by Mass Communication Specialist 2nd Class Indra Beaufort, Dec. 29, 2020.',
          'Tanks: Photo: Tony Webster, CC BY 4.0, via Wikimedia Commons; cropped/resized.',
        ]}
      />
    </AbsoluteFill>
  );
};

const ChallengeBeat: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const cutIn = (start: number) => (frame >= start ? 1 : 0);

  return (
    <AbsoluteFill data-beat-id={'S5-S-02'} style={{backgroundColor: COLORS.ink}}>
      <DocumentaryPlate
        asset='assets/refinery-storage-tanks.jpg'
        objectPosition='52% 50%'
        darkness={0.2}
      />
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(3, 10, 17, 0.12) 0%, rgba(3, 10, 17, 0.5) 23%, rgba(3, 10, 17, 0.84) 52%, rgba(3, 10, 17, 0.72) 100%)',
        }}
      />

      <Eyebrow text='Oil / The rebalance test' />
      <div
        style={{
          position: 'absolute',
          top: 255,
          left: 64,
          right: 64,
          zIndex: 12,
          color: COLORS.challenge,
          fontFamily: DISPLAY_FONT,
          fontSize: 105,
          fontWeight: 900,
          letterSpacing: -1.2,
          lineHeight: 0.92,
          textTransform: 'uppercase',
          textShadow: '0 4px 24px rgba(0, 0, 0, 0.95)',
        }}
      >
        Challenge if
      </div>

      <ConditionRow
        top={500}
        label='Strait'
        detail='Renewed disruption'
        accent={COLORS.challenge}
        opacity={cutIn(8)}
      />
      <ConditionRow
        top={688}
        label='Field supply'
        detail='Slower restarts'
        accent={COLORS.challenge}
        opacity={cutIn(28)}
      />
      <ConditionRow
        top={876}
        label='Inventories'
        detail='Persistent draws'
        accent={COLORS.challenge}
        opacity={cutIn(48)}
      />
      <ConditionRow
        top={1064}
        label='Prices'
        detail='Materially above forecast'
        accent={COLORS.challenge}
        opacity={cutIn(68)}
      />

      <Caption
        visible={captionsVisible}
        text='Renewed disruption, slow restarts, persistent draws, or materially higher prices would challenge it.'
      />
      <SourceRail
        lines={[
          'Conditions: governed-article.',
          'Image: Photo: Tony Webster, CC BY 4.0, via Wikimedia Commons; cropped/resized.',
        ]}
      />
    </AbsoluteFill>
  );
};

const BenchmarkBeat: React.FC<{captionsVisible: boolean}> = ({captionsVisible}) => {
  const frame = useCurrentFrame();
  const wtiReveal = reveal(frame, 1, 6);
  const valueReveal = reveal(frame, 8, 6);
  const dividerReveal = reveal(frame, 22, 6);
  const brentReveal = reveal(frame, 32, 6);
  const checkpointReveal = reveal(frame, 60, 6);
  const closingReveal = reveal(frame, 108, 3);

  return (
    <AbsoluteFill data-beat-id={'S5-S-03'} style={{backgroundColor: COLORS.ink}}>
      <DocumentaryPlate
        asset='assets/refinery-storage-tanks.jpg'
        objectPosition='52% 50%'
        darkness={0.2}
      />
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(2, 8, 14, 0.05) 0%, rgba(2, 8, 14, 0.16) 24%, rgba(2, 8, 14, 0.72) 38%, rgba(2, 8, 14, 0.95) 62%, rgba(2, 8, 14, 0.9) 100%)',
        }}
      />

      <Eyebrow text='Oil / Benchmark boundary' />

      <div
        style={{
          position: 'absolute',
          top: 475,
          left: 64,
          right: 64,
          zIndex: 12,
          opacity: wtiReveal,
        }}
      >
        <div
          style={{
            color: COLORS.confirm,
            fontFamily: TEXT_FONT,
            fontSize: 34,
            fontWeight: 900,
            letterSpacing: 4,
            lineHeight: 1,
            textTransform: 'uppercase',
          }}
        >
          WTI / Observation
        </div>
        <div
          style={{
            marginTop: 15,
            color: COLORS.white,
            fontFamily: DISPLAY_FONT,
            fontSize: 54,
            fontWeight: 900,
            letterSpacing: 1.2,
            lineHeight: 1,
            textTransform: 'uppercase',
          }}
        >
          Jul 6, 2026
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          top: 615,
          left: 64,
          right: 64,
          zIndex: 12,
          overflow: 'hidden',
          clipPath: `inset(0 ${100 - valueReveal * 100}% 0 0)`,
          color: COLORS.white,
          fontFamily: DISPLAY_FONT,
          fontSize: 168,
          fontWeight: 900,
          fontVariantNumeric: 'tabular-nums',
          letterSpacing: -3,
          lineHeight: 0.9,
          textShadow: '0 4px 24px rgba(0, 0, 0, 0.92)',
          whiteSpace: 'nowrap',
        }}
      >
        {'$69.60'}
      </div>

      <div
        style={{
          position: 'absolute',
          top: 820,
          left: 64,
          right: 64,
          zIndex: 12,
          height: 66,
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: 31,
            left: 0,
            width: `${dividerReveal * 100}%`,
            height: 3,
            backgroundColor: COLORS.muted,
          }}
        />
        <div
          style={{
            position: 'absolute',
            top: 7,
            left: 0,
            opacity: dividerReveal,
            paddingRight: 20,
            backgroundColor: '#111a20',
            color: COLORS.muted,
            fontFamily: TEXT_FONT,
            fontSize: 28,
            fontWeight: 900,
            letterSpacing: 3.2,
            textTransform: 'uppercase',
          }}
        >
          Separate benchmarks
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          top: 910,
          left: 64,
          right: 64,
          zIndex: 12,
          opacity: brentReveal,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: 22,
            borderBottom: `2px solid ${COLORS.challenge}`,
            paddingBottom: 12,
          }}
        >
          <div
            style={{
              color: COLORS.challenge,
              fontFamily: DISPLAY_FONT,
              fontSize: 72,
              fontWeight: 900,
              lineHeight: 0.95,
              textTransform: 'uppercase',
            }}
          >
            Brent
          </div>
          <div
            style={{
              color: COLORS.challenge,
              fontFamily: TEXT_FONT,
              fontSize: 30,
              fontWeight: 900,
              letterSpacing: 3.4,
              textTransform: 'uppercase',
            }}
          >
            EIA forecast
          </div>
        </div>
        <div
          style={{
            marginTop: 20,
            color: COLORS.white,
            fontFamily: DISPLAY_FONT,
            fontSize: 51,
            fontWeight: 900,
            letterSpacing: 0.3,
            lineHeight: 1.02,
            textTransform: 'uppercase',
          }}
        >
          WTI does not prove the Brent path
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          top: 1218,
          left: 64,
          right: 64,
          zIndex: 12,
          opacity: checkpointReveal,
        }}
      >
        <div
          style={{
            color: COLORS.muted,
            fontFamily: TEXT_FONT,
            fontSize: 29,
            fontWeight: 900,
            letterSpacing: 4,
            textTransform: 'uppercase',
          }}
        >
          Checkpoints
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 30,
            marginTop: 14,
            borderTop: '2px solid rgba(203, 210, 211, 0.65)',
            paddingTop: 15,
            color: COLORS.white,
            fontFamily: DISPLAY_FONT,
            fontSize: 46,
            fontWeight: 900,
            fontVariantNumeric: 'tabular-nums',
            letterSpacing: 0.4,
            lineHeight: 1,
            textTransform: 'uppercase',
          }}
        >
          <div>Jul 15, 2026</div>
          <div>Aug 11, 2026</div>
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          top: 1450,
          left: 64,
          right: 64,
          zIndex: 12,
          opacity: closingReveal,
          borderLeft: `7px solid ${COLORS.confirm}`,
          paddingLeft: 22,
          color: COLORS.white,
          fontFamily: DISPLAY_FONT,
          fontSize: 53,
          fontWeight: 900,
          letterSpacing: 0.3,
          lineHeight: 0.98,
          textTransform: 'uppercase',
          textShadow: '0 3px 18px rgba(0, 0, 0, 0.96)',
        }}
      >
        <div>Test the conditions,</div>
        <div>not the outcome</div>
      </div>

      <Caption
        visible={captionsVisible}
        text='WTI was $69.60 on July 6 - an observation, not proof. Checkpoints: July 15 and August 11.'
      />
      <SourceRail
        lines={[
          'WTI: fred-dcoilwtico-manifest.',
          'Brent forecast and checkpoints: eia-release-press590.',
          'Interpretation boundary: governed-article.',
        ]}
      />
    </AbsoluteFill>
  );
};

export const Motion_short_9x16_S5_THE_REBALANCE_TEST: React.FC<VariantProps> = ({
  captionsVisible = false,
}) => (
  <AbsoluteFill
    style={{
      backgroundColor: COLORS.ink,
      overflow: 'hidden',
    }}
  >
    <Sequence from={0} durationInFrames={BEAT_1_FRAMES}>
      <ConfirmBeat captionsVisible={captionsVisible} />
    </Sequence>
    <Sequence from={BEAT_1_FRAMES} durationInFrames={BEAT_2_FRAMES}>
      <ChallengeBeat captionsVisible={captionsVisible} />
    </Sequence>
    <Sequence
      from={BEAT_1_FRAMES + BEAT_2_FRAMES}
      durationInFrames={BEAT_3_FRAMES}
    >
      <BenchmarkBeat captionsVisible={captionsVisible} />
    </Sequence>
  </AbsoluteFill>
);
