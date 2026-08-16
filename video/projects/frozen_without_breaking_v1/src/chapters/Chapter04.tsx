import React from 'react';
import {AbsoluteFill, Audio, Easing, Sequence, staticFile, useCurrentFrame} from 'remotion';
import type {ChapterProps} from '../types';
import {
  Canvas,
  ChapterSlug,
  FilmGrain,
  FullBleedImage,
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

const SectorTexture: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const local = frame - start;
  const beat = Math.floor(Math.max(0, local) / 116) % 4;
  const assets = [
    'assets/documentary/grocery_cashier_pexels_4121754.mp4',
    'assets/documentary/finance_team_pexels_7593886.mp4',
    'assets/documentary/warehouse_workers_pexels_4293958.mp4',
    'assets/documentary/office_workers_pexels_6549254.mp4',
  ];
  const labels = ['RETAIL', 'FINANCE', 'LOGISTICS', 'OFFICE WORK'];
  const show = progress(frame, start + 12, start + 48);
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 16)}}>
      {Array.from({length: Math.ceil((end - start) / 116)}, (_, index) => {
        const assetIndex = index % assets.length;
        return (
          <Sequence key={`${assets[assetIndex]}-${index}`} from={start + index * 116} durationInFrames={116} premountFor={12}>
            <FullBleedVideo src={assets[assetIndex]} startFrom={assetIndex === 3 ? 510 : 0} muted style={{filter: 'saturate(.63) brightness(.62) contrast(1.08)', transform: 'scale(1.055)'}} />
          </Sequence>
        );
      })}
      <AbsoluteFill style={{background: 'linear-gradient(90deg,rgba(4,9,12,.91),rgba(4,9,12,.16) 60%,rgba(4,9,12,.65))'}} />
      <ChapterSlug number={4} opacity={show}>One sector holds the ceiling</ChapterSlug>
      <div style={{position: 'absolute', left: 103, top: 210, width: 1120, opacity: show}}>
        <div style={{fontFamily: serif, fontSize: 93, lineHeight: 0.98, letterSpacing: '-.045em'}}>Not just how many.</div>
        <div style={{fontFamily: serif, fontSize: 93, lineHeight: 0.98, letterSpacing: '-.045em', color: copper}}>Where they came from.</div>
      </div>
      <div style={{position: 'absolute', left: 105, bottom: 80, fontFamily: sans, fontSize: 18, letterSpacing: '.17em', color: silver}}>{labels[beat]} · ILLUSTRATIVE FOOTAGE</div>
    </AbsoluteFill>
  );
};

const LoadBearingStructure: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const health = progress(frame, start + 36, start + 78, Easing.out(Easing.cubic));
  const total = progress(frame, start + 148, start + 192, Easing.out(Easing.cubic));
  const rest = progress(frame, start + 270, start + 316, Easing.out(Easing.cubic));
  const equation = progress(frame, start + 302, start + 346, Easing.inOut(Easing.cubic));
  const compression = progress(frame, start + 325, start + 398, Easing.inOut(Easing.cubic));
  const conclusion = progress(frame, start + 404, start + 450, Easing.out(Easing.cubic));
  const warmHandoff = progress(frame, end - 82, end - 26, Easing.inOut(Easing.cubic));
  const floor = 842;
  const beamY = 278 + compression * 18;
  const columnTop = beamY + 66;
  const columnHeight = (floor - columnTop) * health;
  const revealStyle = (amount: number, distance = 18): React.CSSProperties => ({
    opacity: amount,
    transform: `translateY(${(1 - amount) * distance}px)`,
  });
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 18), background: '#091216'}}>
      <AbsoluteFill
        style={{
          background: 'radial-gradient(circle at 31% 54%,rgba(79,181,184,.1),transparent 33%),linear-gradient(115deg,#091216,#071014 68%)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 104,
          top: 72,
          width: 1710,
          fontFamily: serif,
          fontSize: 62,
          letterSpacing: '-.025em',
        }}
      >
        Employment growth became structural load.
      </div>
      <svg width="1920" height="1080" style={{position: 'absolute', inset: 0}}>
        <line x1="112" y1={floor} x2="930" y2={floor} stroke="rgba(241,238,231,.25)" strokeWidth="3" />
        <line x1="112" y1={floor + 12} x2="930" y2={floor + 12} stroke="rgba(241,238,231,.08)" strokeWidth="1" />

        <rect
          x="430"
          y={floor - columnHeight}
          width="172"
          height={columnHeight}
          rx="2"
          fill={cyan}
          fillOpacity={0.82}
        />
        <line x1="454" y1={columnTop} x2="454" y2={floor} stroke="rgba(255,255,255,.24)" strokeWidth="2" opacity={health} />
        <line x1="578" y1={columnTop} x2="578" y2={floor} stroke="rgba(0,0,0,.2)" strokeWidth="2" opacity={health} />

        <rect x="142" y={beamY} width="758" height="66" rx="2" fill={paper} fillOpacity={0.92 * total} />
        <line x1="142" y1={beamY + 66} x2="900" y2={beamY + 66} stroke={copper} strokeWidth="4" opacity={0.7 * total} />

        <path
          d={`M 786 ${beamY - 118} C 786 ${beamY - 62}, 786 ${beamY - 40}, 786 ${beamY - 10}`}
          fill="none"
          stroke={red}
          strokeWidth="5"
          strokeDasharray="10 11"
          opacity={rest}
        />
        <path d={`M 768 ${beamY - 22} L 786 ${beamY + 2} L 804 ${beamY - 22}`} fill={red} opacity={rest} />
        <line x1="142" y1={beamY - 2} x2="900" y2={beamY - 2} stroke="rgba(230,90,91,.32)" strokeWidth="2" opacity={compression} />
      </svg>

      <div
        style={{
          position: 'absolute',
          left: 142,
          top: beamY + 18,
          width: 758,
          textAlign: 'center',
          fontFamily: sans,
          fontSize: 15,
          fontWeight: 760,
          letterSpacing: '.16em',
          color: '#263237',
          opacity: total,
        }}
      >
        TOTAL NET PAYROLL CHANGE
      </div>
      <div
        style={{
          position: 'absolute',
          left: 430,
          top: 576,
          width: 172,
          textAlign: 'center',
          fontFamily: sans,
          fontSize: 15,
          fontWeight: 760,
          lineHeight: 1.25,
          letterSpacing: '.14em',
          color: '#052025',
          opacity: health,
        }}
      >
        HEALTH<br />CARE
      </div>

      <div
        style={{
          position: 'absolute',
          left: 1018,
          top: 238,
          width: 786,
          height: 454,
          boxSizing: 'border-box',
          padding: '30px 34px 28px',
          borderTop: '1px solid rgba(241,238,231,.22)',
          borderBottom: '1px solid rgba(241,238,231,.22)',
          background: 'linear-gradient(90deg,rgba(255,255,255,.025),rgba(255,255,255,.055),rgba(255,255,255,.025))',
        }}
      >
        <div style={{fontFamily: sans, fontSize: 16, letterSpacing: '.18em', color: silver}}>TWELVE-MONTH PAYROLL ARITHMETIC</div>
        <div style={{position: 'absolute', left: 34, right: 34, top: 104, display: 'flex', alignItems: 'flex-start'}}>
          <div style={{width: 198, ...revealStyle(health)}}>
            <div style={{fontFamily: sans, fontSize: 72, lineHeight: 0.96, fontWeight: 830, letterSpacing: '-.06em', color: cyan}}>+392K</div>
            <div style={{marginTop: 18, fontFamily: sans, fontSize: 16, lineHeight: 1.35, letterSpacing: '.12em', color: silver}}>HEALTH CARE</div>
          </div>
          <div style={{width: 38, paddingTop: 16, textAlign: 'center', fontFamily: serif, fontSize: 50, color: silver, opacity: equation}}>+</div>
          <div style={{width: 195, ...revealStyle(rest)}}>
            <div style={{fontFamily: sans, fontSize: 72, lineHeight: 0.96, fontWeight: 830, letterSpacing: '-.06em', color: red}}>−76K</div>
            <div style={{marginTop: 18, fontFamily: sans, fontSize: 16, lineHeight: 1.35, letterSpacing: '.1em', color: silver}}>ALL OTHER SECTORS<br />COMBINED</div>
          </div>
          <div style={{width: 38, paddingTop: 16, textAlign: 'center', fontFamily: serif, fontSize: 50, color: silver, opacity: equation}}>=</div>
          <div style={{width: 249, textAlign: 'right', ...revealStyle(total)}}>
            <div style={{fontFamily: sans, fontSize: 72, lineHeight: 0.96, fontWeight: 830, letterSpacing: '-.06em', color: paper}}>+316K</div>
            <div style={{marginTop: 18, fontFamily: sans, fontSize: 16, lineHeight: 1.35, letterSpacing: '.1em', color: silver}}>TOTAL PAYROLLS</div>
          </div>
        </div>
        <div
          style={{
            position: 'absolute',
            left: 34,
            right: 34,
            bottom: 30,
            paddingTop: 18,
            borderTop: '1px solid rgba(241,238,231,.14)',
            fontFamily: serif,
            fontSize: 28,
            lineHeight: 1.25,
            color: paper,
            ...revealStyle(conclusion, 10),
          }}
        >
          Health care exceeded the net gain because the rest of the economy summed negative.
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          left: 142,
          bottom: 116,
          width: 758,
          fontFamily: serif,
          fontSize: 31,
          lineHeight: 1.3,
          color: paper,
          ...revealStyle(conclusion, 10),
        }}
      >
        One load-bearing sector. Not the only sector growing.
      </div>
      <AbsoluteFill
        style={{
          pointerEvents: 'none',
          opacity: warmHandoff,
          background: 'radial-gradient(circle at 29% 55%,rgba(214,137,60,.2),transparent 28%)',
        }}
      />
      <SourceTag>BLS PAYROLL EMPLOYMENT · JULY 2025–JULY 2026 · CALCULATION FROM OFFICIAL LEVELS</SourceTag>
    </AbsoluteFill>
  );
};

const HealthcareBreath: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const halfway = start + (end - start) * 0.46;
  const conceptual = 1 - progress(frame, halfway - 18, halfway + 26, Easing.inOut(Easing.cubic));
  const real = progress(frame, halfway - 22, halfway + 24, Easing.inOut(Easing.cubic));
  const zoom = 1.03 + progress(frame, start, end) * 0.05;
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 18), background: ink}}>
      <AbsoluteFill style={{opacity: conceptual}}>
        <FullBleedImage src="assets/illustrative/load_bearing_healthcare_imagegen_v1.png" zoom={zoom} style={{filter: 'saturate(.78) brightness(.75)'}} />
        <AbsoluteFill style={{background: 'linear-gradient(90deg,rgba(4,9,12,.68),transparent 64%)'}} />
        <div style={{position: 'absolute', left: 102, top: 112, width: 640}}>
          <div style={{fontFamily: sans, fontSize: 17, letterSpacing: '.16em', color: amber}}>CONCEPTUAL ILLUSTRATION</div>
          <div style={{fontFamily: serif, fontSize: 65, lineHeight: 1.02, marginTop: 28}}>One warm station.<br />One load-bearing column.</div>
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{opacity: real}}>
        <FullBleedVideo src="assets/documentary/healthcare_nurse_pexels_6130024.mp4" startFrom={60} muted style={{filter: 'saturate(.84) brightness(.72)', transform: 'scale(1.035)'}} />
        <AbsoluteFill style={{background: 'linear-gradient(90deg,rgba(4,9,12,.56),transparent 55%,rgba(4,9,12,.2))'}} />
        <div style={{position: 'absolute', left: 103, bottom: 88, width: 520, fontFamily: serif, fontSize: 36, lineHeight: 1.3}}>Care is labor-intensive, skilled, physical work.</div>
        <SourceTag>ILLUSTRATIVE WORKPLACE FOOTAGE · NOT A MEASURED FACILITY</SourceTag>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const BreadthCounterweight: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const dial = progress(frame, start + 22, start + 104, Easing.out(Easing.cubic));
  const pressure = progress(frame, start + 145, start + 205);
  const finish = progress(frame, start + 410, start + 462, Easing.out(Easing.cubic));
  const close = progress(frame, end - 98, end - 48, Easing.inOut(Easing.cubic));
  const question = progress(frame, end - 82, end - 48, Easing.out(Easing.cubic));
  const angle = -130 + dial * 262;
  const points = [
    {label: 'RETAIL', value: '−19K'},
    {label: 'FINANCIAL ACTIVITIES', value: '−14K'},
    {label: 'LOCAL GOV. EDUCATION', value: '≈−50K'},
  ];
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 16), background: paper, color: ink}}>
      <div style={{position: 'absolute', left: 100, top: 78, fontFamily: serif, fontSize: 65}}>Breadth was near balance. Magnitude was not.</div>
      <div style={{position: 'absolute', left: 122, top: 280, width: 530, height: 530, borderRadius: '50%', border: '2px solid rgba(8,16,21,.18)'}}>
        <div style={{position: 'absolute', left: 262, top: 262, width: 214, height: 4, background: copper, transformOrigin: '0 50%', transform: `rotate(${angle}deg)`}} />
        <div style={{position: 'absolute', left: 249, top: 249, width: 28, height: 28, background: ink, borderRadius: '50%'}} />
        <div style={{position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', paddingTop: 80}}>
          <div style={{textAlign: 'center'}}>
            <div style={{fontFamily: sans, fontSize: 108, fontWeight: 820, letterSpacing: '-.06em'}}>51.8</div>
            <div style={{fontFamily: sans, fontSize: 16, letterSpacing: '.14em'}}>PRIVATE DIFFUSION INDEX</div>
            <div style={{fontFamily: serif, fontSize: 25, marginTop: 12, color: '#566469'}}>50 = neutral breadth</div>
          </div>
        </div>
      </div>
      <div style={{position: 'absolute', right: 108, top: 272, width: 760}}>
        <div style={{fontFamily: sans, fontSize: 18, letterSpacing: '.16em', color: red, opacity: pressure}}>SELECTED PRESSURE POINTS · JULY</div>
        {points.map((point, index) => (
          <div key={point.label} style={{display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', padding: '26px 0', borderBottom: '1px solid rgba(8,16,21,.14)', opacity: progress(frame, start + 152 + index * 18, start + 185 + index * 18)}}>
            <span style={{fontFamily: sans, fontSize: 20, letterSpacing: '.08em'}}>{point.label}</span>
            <span style={{fontFamily: sans, fontSize: 57, fontWeight: 800, color: red}}>{point.value}</span>
          </div>
        ))}
      </div>
      <div style={{position: 'absolute', right: 108, bottom: 82, width: 780, fontFamily: serif, fontSize: 34, lineHeight: 1.32, color: '#263237', opacity: finish}}>
        Construction, professional services, and leisure and hospitality were positive. The claim is concentration—not universal contraction.
      </div>
      <SourceTag color="#536267">BLS · JULY 2026 · PRIVATE DIFFUSION AND INDUSTRY DETAIL</SourceTag>
      <AbsoluteFill style={{opacity: close, background: paper, display: 'grid', placeItems: 'center'}}>
        <div style={{fontFamily: serif, fontSize: 57, letterSpacing: '-.02em', color: ink, opacity: question}}>So why has it not stopped?</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Chapter04: React.FC<ChapterProps> = ({durationInFrames}) => {
  const a = Math.round(durationInFrames * 0.14);
  const b = Math.round(durationInFrames * 0.4);
  const c = Math.round(durationInFrames * 0.7);
  const nurseBreath = b + (c - b) * 0.46;
  return (
    <Canvas>
      <SectorTexture start={0} end={a + 14} />
      <LoadBearingStructure start={a - 12} end={b + 18} />
      <HealthcareBreath start={b - 12} end={c + 16} />
      <BreadthCounterweight start={c - 12} end={durationInFrames} />
      <Audio src={staticFile('assets/audio/narration/chapter_04.wav')} volume={1} />
      <Audio
        src={staticFile('assets/audio/sound/chapter_04_bed.m4a')}
        volume={(f) => {
          const down = progress(f, nurseBreath - 32, nurseBreath + 8);
          const up = progress(f, c - 24, c + 18);
          return 0.78 * Math.min(1, 1 - down + up);
        }}
      />
      <Vignette strength={0.4} />
      <FilmGrain opacity={0.08} />
    </Canvas>
  );
};
