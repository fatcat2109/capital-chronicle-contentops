import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import type {ChapterProps} from '../types';
import {
  Canvas,
  ChapterSlug,
  FilmGrain,
  FullBleedVideo,
  SourceTag,
  Vignette,
  amber,
  copper,
  cyan,
  holdFade,
  ink,
  paper,
  progress,
  red,
  sans,
  serif,
  silver,
} from '../shared';

const WarehouseField: React.FC<{opacity: number}> = ({opacity}) => {
  const frame = useCurrentFrame();
  const drift = interpolate(frame, [0, 260], [1.04, 1.12], {
    extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill style={{opacity}}>
      <FullBleedVideo
        src="assets/documentary/warehouse_workers_pexels_4293958.mp4"
        muted
        style={{transform: `scale(${drift})`, filter: 'saturate(.72) contrast(1.08)'}}
      />
      <AbsoluteFill
        style={{background: 'linear-gradient(90deg, rgba(5,12,16,.88), rgba(5,12,16,.08) 64%, rgba(5,12,16,.55))'}}
      />
    </AbsoluteFill>
  );
};

const OutputHours: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const draw = progress(frame, start + 8, start + 95, Easing.out(Easing.cubic));
  const reveal = progress(frame, start, start + 18);
  const gap = progress(frame, start + 45, start + 112, Easing.inOut(Easing.cubic));
  const width = 1160;
  const x = 380;
  const y = 620;
  const outputY = y - 260 * gap;
  const hoursY = y - 28 * gap;
  const labelOpacity = progress(frame, start + 76, start + 96);
  const gapOpacity = progress(frame, start + 105, start + 124);
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 16)}}>
      <div
        style={{
          position: 'absolute',
          left: 112,
          top: 105,
          fontFamily: serif,
          fontSize: 74,
          lineHeight: 1.02,
          letterSpacing: '-0.035em',
          color: paper,
          opacity: reveal,
        }}
      >
        Output moved.
        <br />
        Hours barely did.
      </div>
      <svg width="1920" height="1080" style={{position: 'absolute', inset: 0}}>
        <defs>
          <linearGradient id="output" x1="0" x2="1">
            <stop stopColor={cyan} />
            <stop offset="1" stopColor={paper} />
          </linearGradient>
          <linearGradient id="hours" x1="0" x2="1">
            <stop stopColor={copper} />
            <stop offset="1" stopColor={amber} />
          </linearGradient>
        </defs>
        <line x1={x} y1={y} x2={x + width} y2={y} stroke="rgba(241,238,231,.16)" />
        <line
          x1={x}
          y1={y}
          x2={x + width * draw}
          y2={y + (outputY - y) * draw}
          stroke="url(#output)"
          strokeWidth="8"
          strokeLinecap="round"
        />
        <line
          x1={x}
          y1={y}
          x2={x + width * draw}
          y2={y + (hoursY - y) * draw}
          stroke="url(#hours)"
          strokeWidth="5"
          strokeLinecap="round"
        />
        <path
          d={`M ${x + width - 48} ${outputY + 20} L ${x + width - 48} ${hoursY - 20}`}
          stroke={paper}
          strokeOpacity={0.36 * gapOpacity}
          strokeDasharray="7 9"
        />
      </svg>
      <div style={{position: 'absolute', right: 178, top: outputY - 56, opacity: labelOpacity}}>
        <div style={{fontFamily: sans, fontSize: 72, fontWeight: 720, color: cyan}}>+2.5%</div>
        <div style={{fontFamily: sans, fontSize: 20, letterSpacing: '.13em', color: silver}}>OUTPUT · YEAR OVER YEAR</div>
      </div>
      <div style={{position: 'absolute', right: 178, top: hoursY + 32, opacity: labelOpacity}}>
        <div style={{fontFamily: sans, fontSize: 58, fontWeight: 700, color: copper}}>+0.2%</div>
        <div style={{fontFamily: sans, fontSize: 20, letterSpacing: '.13em', color: silver}}>HOURS · YEAR OVER YEAR</div>
      </div>
      <div
        style={{
          position: 'absolute',
          left: 770,
          top: 640,
          opacity: gapOpacity,
          fontFamily: serif,
          color: paper,
          fontSize: 48,
          fontStyle: 'italic',
        }}
      >
        the gap is productivity
        <span style={{color: cyan, marginLeft: 22, fontFamily: sans, fontStyle: 'normal', fontWeight: 720}}>+2.2%</span>
      </div>
      <SourceTag>BLS · NONFARM BUSINESS · Q2 2026 PRELIMINARY</SourceTag>
    </AbsoluteFill>
  );
};

const MeasurementNotMotive: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const t = progress(frame, start + 15, start + 55, Easing.out(Easing.cubic));
  const words = ['CAPITAL', 'INDUSTRY MIX', 'WORKER COMPOSITION', 'CYCLICAL CHOICE', 'MEASUREMENT'];
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 18), background: ink}}>
      <div
        style={{
          position: 'absolute',
          left: 108,
          top: 128,
          fontFamily: sans,
          fontSize: 25,
          fontWeight: 720,
          letterSpacing: '.17em',
          color: copper,
        }}
      >
        MEASUREMENT ≠ MOTIVE
      </div>
      <div
        style={{
          position: 'absolute',
          left: 108,
          top: 215,
          width: 1120,
          fontFamily: serif,
          fontSize: 82,
          lineHeight: 1.03,
          letterSpacing: '-.04em',
          color: paper,
        }}
      >
        Output divided by hours
        <br />
        does not name the cause.
      </div>
      <div style={{position: 'absolute', left: 111, top: 560, width: 1660, height: 230}}>
        {words.map((word, index) => {
          const local = progress(frame, start + 42 + index * 8, start + 70 + index * 8);
          return (
            <span
              key={word}
              style={{
                position: 'absolute',
                left: index * 300 + Math.sin(index * 3.1) * 22,
                top: 28 + (index % 2) * 84,
                fontFamily: sans,
                fontSize: 19,
                fontWeight: 650,
                letterSpacing: '.12em',
                color: index === 4 ? cyan : silver,
                opacity: local * (0.9 - index * 0.06),
                transform: `translateY(${(1 - local) * 18}px)`,
              }}
            >
              {word}
            </span>
          );
        })}
      </div>
      <div
        style={{
          position: 'absolute',
          right: 124,
          bottom: 103,
          width: 340,
          height: 340,
          border: `1px solid rgba(119,200,194,${0.26 * t})`,
          borderRadius: '50%',
          transform: `scale(${0.78 + 0.22 * t})`,
        }}
      >
        <div style={{position: 'absolute', inset: 54, border: '1px solid rgba(241,238,231,.18)', borderRadius: '50%'}} />
        <div style={{position: 'absolute', inset: 120, background: cyan, borderRadius: '50%', opacity: 0.76}} />
      </div>
    </AbsoluteFill>
  );
};

const DemandMontage: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const local = frame - start;
  const beat = Math.floor(local / 135) % 3;
  const assets = [
    'assets/documentary/grocery_cashier_pexels_4121754.mp4',
    'assets/documentary/office_workers_pexels_6549254.mp4',
    'assets/documentary/warehouse_workers_pexels_4293958.mp4',
  ];
  const reveal = progress(frame, start + 55, start + 105);
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 15)}}>
      {Array.from({length: Math.ceil((end - start) / 135)}, (_, index) => {
        const assetIndex = index % assets.length;
        return (
          <Sequence key={`${assets[assetIndex]}-${index}`} from={start + index * 135} durationInFrames={135} premountFor={12}>
            <FullBleedVideo
              src={assets[assetIndex]}
              startFrom={assetIndex === 1 ? 360 : 0}
              muted
              style={{filter: 'saturate(.82) contrast(1.06)', transform: 'scale(1.035)'}}
            />
          </Sequence>
        );
      })}
      <AbsoluteFill style={{background: 'linear-gradient(90deg,rgba(4,10,13,.8),rgba(4,10,13,.08) 58%,rgba(4,10,13,.74))'}} />
      <div
        style={{
          position: 'absolute',
          left: 112,
          bottom: 136,
          display: 'flex',
          gap: 76,
          alignItems: 'flex-end',
          opacity: reveal,
        }}
      >
        <div>
          <div style={{fontFamily: sans, fontSize: 88, fontWeight: 760, color: paper}}>+1.5%</div>
          <div style={{fontFamily: sans, fontSize: 20, letterSpacing: '.13em', color: silver}}>REAL GDP · Q2 ANNUAL RATE</div>
        </div>
        <div style={{width: 1, height: 126, background: 'rgba(241,238,231,.28)'}} />
        <div>
          <div style={{fontFamily: sans, fontSize: 108, fontWeight: 760, color: amber}}>+3.9%</div>
          <div style={{fontFamily: sans, fontSize: 20, letterSpacing: '.13em', color: paper}}>PRIVATE DOMESTIC FINAL SALES · Q2</div>
        </div>
      </div>
      <SourceTag>BEA · ADVANCE ESTIMATE · Q2 2026</SourceTag>
    </AbsoluteFill>
  );
};

const FinalSplit: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const op = holdFade(frame, start, end, 18);
  const move = progress(frame, start, start + 120, Easing.out(Easing.cubic));
  return (
    <AbsoluteFill style={{opacity: op, background: ink}}>
      <div style={{position: 'absolute', inset: 0, width: '52%', overflow: 'hidden'}}>
        <FullBleedVideo
          src="assets/documentary/office_workers_pexels_6549254.mp4"
          startFrom={870}
          muted
          style={{width: '1920px', maxWidth: 'none', transform: `translateX(${-190 - move * 45}px) scale(1.08)`, filter: 'saturate(.7) brightness(.78)'}}
        />
      </div>
      <div
        style={{
          position: 'absolute',
          left: '52%',
          top: 0,
          bottom: 0,
          width: 2,
          background: copper,
          opacity: 0.7,
        }}
      />
      <div style={{position: 'absolute', left: '58%', top: 168, width: 650}}>
        <div style={{fontFamily: sans, fontSize: 20, letterSpacing: '.15em', color: cyan, marginBottom: 34}}>AGGREGATE RESILIENCE</div>
        <div style={{fontFamily: serif, fontSize: 78, lineHeight: 1.04, letterSpacing: '-.035em', color: paper}}>
          is not the same as
          <br />
          broad opportunity.
        </div>
        <div style={{marginTop: 64, width: 92, height: 3, background: copper}} />
      </div>
    </AbsoluteFill>
  );
};

export const Chapter05: React.FC<ChapterProps> = ({durationInFrames}) => {
  const frame = useCurrentFrame();
  const b1 = Math.round(durationInFrames * 0.16);
  const b2 = Math.round(durationInFrames * 0.39);
  const b3 = Math.round(durationInFrames * 0.59);
  const b4 = Math.round(durationInFrames * 0.83);
  return (
    <Canvas>
      <WarehouseField opacity={1 - progress(frame, b1 - 18, b1 + 12)} />
      <div
        style={{
          position: 'absolute',
          left: 104,
          top: 190,
          width: 860,
          fontFamily: serif,
          fontSize: 104,
          lineHeight: 0.98,
          letterSpacing: '-.05em',
          color: paper,
          opacity: holdFade(frame, 4, b1, 20),
        }}
      >
        The machine
        <br />
        keeps running.
      </div>
      <ChapterSlug number={5} opacity={holdFade(frame, 0, 105, 15)}>The machine keeps running</ChapterSlug>
      <OutputHours start={b1 - 8} end={b2 + 14} />
      <MeasurementNotMotive start={b2 - 7} end={b3 + 12} />
      <DemandMontage start={b3 - 8} end={b4 + 12} />
      <FinalSplit start={b4 - 7} end={durationInFrames} />

      <Audio src={staticFile('assets/audio/narration/chapter_05.wav')} volume={1} />
      <Audio src={staticFile('assets/audio/sound/chapter_05_bed.m4a')} volume={0.78} />
      <Vignette strength={0.48} />
      <FilmGrain opacity={0.085} />
      <AbsoluteFill style={{pointerEvents: 'none', border: '1px solid rgba(241,238,231,.04)'}} />
    </Canvas>
  );
};
