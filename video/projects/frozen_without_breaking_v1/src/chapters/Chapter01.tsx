import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import type {ChapterProps} from '../types';
import {
  Canvas,
  FilmGrain,
  FullBleedImage,
  SourceTag,
  Vignette,
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

const AuthorityOpen: React.FC = () => {
  const frame = useCurrentFrame();
  const pictureIn = 21;
  const pictureOut = 470;
  const roomToneOut = 481;
  const appear = progress(frame, pictureIn + 2, pictureIn + 18, Easing.out(Easing.quad));
  const quotation = progress(frame, 262, 284, Easing.out(Easing.cubic));
  return (
    <AbsoluteFill style={{background: '#050A0E'}}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 70% 43%, rgba(38,52,77,.26), transparent 48%), linear-gradient(90deg,#020506 0%,#081016 37%,#030608 100%)',
        }}
      />
      <div style={{position: 'absolute', left: 690, top: 72, bottom: 70, width: 1, background: 'rgba(184,111,72,.34)', opacity: appear}} />
      <div
        style={{
          position: 'absolute',
          left: 112,
          top: 126,
          width: 500,
          fontFamily: sans,
          color: paper,
          opacity: appear,
        }}
      >
        <div style={{fontSize: 18, letterSpacing: '.21em', color: copper, fontWeight: 700}}>JULY 29, 2026</div>
        <div style={{fontFamily: serif, fontSize: 70, lineHeight: 0.99, letterSpacing: '-.035em', marginTop: 28}}>
          What was knowable<br />in real time.
        </div>
        <div style={{display: 'flex', alignItems: 'center', gap: 18, marginTop: 40}}>
          <div style={{width: 72, height: 2, background: copper}} />
          <div style={{fontSize: 15, letterSpacing: '.16em', color: silver}}>DATED AUTHORITY</div>
        </div>
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: 520,
            width: 500,
            borderTop: '1px solid rgba(241,238,231,.18)',
            paddingTop: 22,
            opacity: quotation,
            transform: `translateY(${(1 - quotation) * 10}px)`,
          }}
        >
          <div style={{fontSize: 14, letterSpacing: '.18em', color: copper, fontWeight: 700}}>CONTEMPORANEOUS ASSESSMENT</div>
          <div style={{fontFamily: serif, fontSize: 35, lineHeight: 1.18, color: paper, marginTop: 15}}>
            “Job gains have kept pace<br />with the workforce.”
          </div>
        </div>
      </div>
      <div
        style={{
          position: 'absolute',
          left: 748,
          top: 72,
          width: 1056,
          height: 864,
          overflow: 'hidden',
          boxShadow: '0 30px 94px rgba(0,0,0,.52)',
        }}
      >
        <OffthreadVideo
          src={staticFile('assets/authority/fed_fomc_2026-07-29_clip01_labor_baseline_official_880x720_handles.mp4')}
          muted={false}
          volume={(f) => Math.min(progress(f, 0, 8), 1 - progress(f, pictureOut, roomToneOut))}
          style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'center'}}
        />
        <AbsoluteFill style={{boxShadow: 'inset 0 0 0 1px rgba(241,238,231,.12)'}} />
      </div>
      <div
        style={{
          position: 'absolute',
          left: 748,
          top: 960,
          width: 1056,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
          fontFamily: sans,
          fontSize: 15,
          lineHeight: 1.4,
          letterSpacing: '.11em',
          color: silver,
          opacity: appear,
          textTransform: 'uppercase',
        }}
      >
        <span><strong style={{color: paper, fontWeight: 750}}>Kevin Warsh</strong> · Chairman, Federal Reserve</span>
        <span style={{fontSize: 13, color: 'rgba(184,196,198,.72)'}}>Official FOMC press conference</span>
      </div>
      <div
        style={{
          position: 'absolute',
          left: 748,
          top: 1002,
          width: 1056,
          fontFamily: sans,
          fontSize: 12,
          letterSpacing: '.09em',
          color: 'rgba(184,196,198,.55)',
          opacity: appear,
          textTransform: 'uppercase',
        }}
      >
        Board of Governors of the Federal Reserve System
      </div>
      {(frame < pictureIn || frame >= pictureOut) && <AbsoluteFill style={{background: '#020507'}} />}
    </AbsoluteFill>
  );
};

const HeadlineParadox: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const local = frame - start;
  const nine = holdFade(frame, start, start + 92, 12);
  const facts = progress(frame, start + 76, start + 124);
  const collide = progress(frame, start + 156, start + 230, Easing.inOut(Easing.cubic));
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 16), background: paper, color: ink}}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.1,
          backgroundImage: 'repeating-linear-gradient(0deg,transparent 0 31px,rgba(8,16,21,.12) 32px)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 98,
          top: 86,
          fontFamily: sans,
          fontWeight: 800,
          fontSize: 25,
          letterSpacing: '.22em',
          color: red,
          opacity: nine,
        }}
      >
        NINE DAYS LATER
      </div>
      <div style={{position: 'absolute', left: 98, top: 202, width: 1720, display: 'flex', justifyContent: 'space-between'}}>
        <div style={{opacity: facts, transform: `translateX(${(1 - facts) * -55}px)`}}>
          <div style={{fontFamily: sans, fontSize: 180, fontWeight: 800, letterSpacing: '-.07em', color: red}}>−23,000</div>
          <div style={{fontFamily: serif, fontSize: 38, color: '#273238'}}>payroll jobs · July</div>
        </div>
        <div
          style={{
            textAlign: 'right',
            opacity: facts,
            transform: `translateX(${(1 - facts) * 55}px)`,
          }}
        >
          <div style={{fontFamily: sans, fontSize: 180, fontWeight: 800, letterSpacing: '-.07em', color: ink}}>4.1%</div>
          <div style={{fontFamily: serif, fontSize: 38, color: '#273238'}}>unemployment rate · July</div>
        </div>
      </div>
      <div
        style={{
          position: 'absolute',
          left: 98 + collide * 594,
          right: 98 + collide * 594,
          bottom: 180,
          height: 2,
          background: `linear-gradient(90deg,${red},${ink})`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 86,
          textAlign: 'center',
          fontFamily: sans,
          fontSize: 20,
          letterSpacing: '.18em',
          color: '#4C5A5E',
          opacity: progress(frame, start + 190, start + 222),
        }}
      >
        TWO OFFICIAL SURVEYS · TWO DIFFERENT OBJECTS
      </div>
      <SourceTag color="#536267">BLS EMPLOYMENT SITUATION · RELEASED AUGUST 7, 2026</SourceTag>
    </AbsoluteFill>
  );
};

const RevisionPaper: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const step1 = progress(frame, start + 25, start + 52);
  const step2 = progress(frame, start + 102, start + 132);
  const step3 = progress(frame, start + 185, start + 215);
  const combined = progress(frame, start + 260, start + 300);
  const row = (label: string, first: string, second: string, last: string, y: number, june = false) => (
    <div style={{position: 'absolute', left: 184, top: y, right: 180, height: 176}}>
      <div style={{fontFamily: sans, fontSize: 20, letterSpacing: '.18em', fontWeight: 750, color: silver}}>{label}</div>
      <div style={{display: 'flex', alignItems: 'baseline', gap: 34, marginTop: 21}}>
        <span style={{fontFamily: sans, fontSize: 82, color: 'rgba(241,238,231,.28)', textDecoration: 'line-through', opacity: step1}}>{first}</span>
        <span style={{fontFamily: serif, fontSize: 39, color: silver, opacity: step2}}>→</span>
        {!june && <span style={{fontFamily: sans, fontSize: 82, color: 'rgba(241,238,231,.48)', textDecoration: 'line-through', opacity: step2}}>{second}</span>}
        {!june && <span style={{fontFamily: serif, fontSize: 39, color: silver, opacity: step3}}>→</span>}
        <span style={{fontFamily: sans, fontSize: 112, fontWeight: 800, color: red, opacity: step3}}>{last}</span>
      </div>
    </div>
  );
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 18), background: '#10171B'}}>
      <div style={{position: 'absolute', left: 92, top: 68, fontFamily: serif, fontSize: 58, color: paper}}>The past moved.</div>
      <div style={{position: 'absolute', right: 92, top: 82, fontFamily: sans, fontSize: 18, letterSpacing: '.14em', color: copper}}>PAYROLL RELEASE VINTAGES</div>
      <div style={{position: 'absolute', left: 92, right: 92, top: 162, bottom: 96, borderTop: '1px solid rgba(241,238,231,.18)', borderBottom: '1px solid rgba(241,238,231,.18)'}} />
      {row('MAY 2026', '+172K', '+129K', '+63K', 245)}
      {row('JUNE 2026', '+57K', '', '+20K', 505, true)}
      <div
        style={{
          position: 'absolute',
          right: 118,
          bottom: 84,
          fontFamily: sans,
          color: red,
          opacity: combined,
          transform: `translateY(${(1 - combined) * 16}px)`,
        }}
      >
        <span style={{fontSize: 72, fontWeight: 800}}>−103K</span>
        <span style={{fontSize: 18, letterSpacing: '.12em', marginLeft: 22}}>MAY + JUNE · JULY RELEASE REVISION</span>
      </div>
      <SourceTag>BLS ARCHIVED EMPLOYMENT SITUATION RELEASES</SourceTag>
    </AbsoluteFill>
  );
};

const UncertaintyField: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const local = progress(frame, start, end);
  const dot = progress(frame, start + 22, start + 68, Easing.out(Easing.cubic));
  const future = progress(frame, start + 210, start + 255);
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 18), background: ink}}>
      <div style={{position: 'absolute', left: 108, top: 100, fontFamily: serif, fontSize: 71, lineHeight: 1.02}}>
        One print is a point.<br />Alignment is a condition.
      </div>
      <svg width="1920" height="1080" style={{position: 'absolute', inset: 0}}>
        <line x1="160" y1="640" x2="1760" y2="640" stroke="rgba(241,238,231,.18)" strokeWidth="2" />
        <rect x="610" y="600" width="700" height="80" fill="rgba(216,74,69,.08)" stroke="rgba(216,74,69,.28)" strokeDasharray="8 9" />
        <circle cx={960 - 430 * dot} cy="640" r="15" fill={red} />
        <line x1="960" y1="564" x2="960" y2="716" stroke="rgba(241,238,231,.3)" />
      </svg>
      <div style={{position: 'absolute', left: 484, top: 713, fontFamily: sans, fontSize: 23, color: red, opacity: dot}}>−23K</div>
      <div style={{position: 'absolute', left: 748, top: 720, width: 430, textAlign: 'center', fontFamily: sans, fontSize: 18, lineHeight: 1.5, letterSpacing: '.08em', color: silver}}>
        APPROX. ±122K NEEDED<br />FOR THE USUAL 90% THRESHOLD
      </div>
      <div
        style={{
          position: 'absolute',
          right: 108,
          top: 176,
          width: 490,
          padding: '30px 34px',
          borderLeft: `3px solid ${copper}`,
          background: 'rgba(241,238,231,.04)',
          opacity: future,
        }}
      >
        <div style={{fontFamily: sans, fontSize: 18, letterSpacing: '.15em', color: copper}}>NEXT DATA CLIFF</div>
        <div style={{fontFamily: serif, fontSize: 48, marginTop: 17}}>August 28</div>
        <div style={{fontFamily: sans, fontSize: 21, color: silver, marginTop: 12, lineHeight: 1.45}}>Preliminary payroll benchmark<br />against tax records</div>
      </div>
      <div
        style={{position: 'absolute', left: 108, bottom: 78, fontFamily: sans, fontSize: 18, color: silver, letterSpacing: '.08em', opacity: 0.65 + local * 0.25}}
      >
        PRECISION IS NOT THE CLAIM. CONVERGENCE IS.
      </div>
    </AbsoluteFill>
  );
};

const TitleField: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const local = progress(frame, start, end);
  const zoom = 1.02 + local * 0.06;
  const title = progress(frame, start + 28, start + 74, Easing.out(Easing.cubic));
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 18)}}>
      <FullBleedImage
        src="assets/illustrative/frozen_concourse_imagegen_v1.png"
        zoom={zoom}
        x={-18 * local}
        style={{filter: 'saturate(.78) contrast(1.05) brightness(.72)'}}
      />
      <AbsoluteFill style={{background: 'linear-gradient(90deg,rgba(3,8,11,.82),rgba(3,8,11,.2) 63%,rgba(3,8,11,.62))'}} />
      <div
        style={{
          position: 'absolute',
          left: 104,
          top: 185,
          width: 1180,
          opacity: title,
          transform: `translateY(${(1 - title) * 28}px)`,
        }}
      >
        <div style={{fontFamily: serif, fontSize: 136, lineHeight: 0.91, letterSpacing: '-.06em', color: paper}}>
          Frozen
          <br />
          <span style={{color: copper}}>without breaking.</span>
        </div>
        <div style={{marginTop: 46, width: 700, fontFamily: sans, fontSize: 24, lineHeight: 1.5, letterSpacing: '.04em', color: silver}}>
          HOW THE ECONOMY KEPT GROWING AS JOB CREATION<br />AND WORKER MOBILITY STALLED
        </div>
      </div>
      <SourceTag>GENERATED CONCEPTUAL ILLUSTRATION · NOT DOCUMENTARY EVIDENCE</SourceTag>
    </AbsoluteFill>
  );
};

export const Chapter01: React.FC<ChapterProps> = ({durationInFrames}) => {
  const introEnd = 505;
  const h1 = Math.round(durationInFrames * 0.33);
  const h2 = Math.round(durationInFrames * 0.60);
  const h3 = Math.round(durationInFrames * 0.82);
  return (
    <Canvas>
      <Sequence from={0} durationInFrames={483} premountFor={20}><AuthorityOpen /></Sequence>
      <HeadlineParadox start={introEnd - 10} end={h1 + 20} />
      <RevisionPaper start={h1 - 12} end={h2 + 18} />
      <UncertaintyField start={h2 - 12} end={h3 + 18} />
      <TitleField start={h3 - 10} end={durationInFrames} />

      <Audio src={staticFile('assets/audio/narration/chapter_01.wav')} volume={1} />
      <Sequence from={introEnd} durationInFrames={Math.max(1, durationInFrames - introEnd)}>
        <Audio src={staticFile('assets/audio/sound/chapter_01_bed.m4a')} volume={0.62} startFrom={introEnd} />
      </Sequence>
      <Sequence from={introEnd + 8} durationInFrames={28}>
        <Audio src={staticFile('assets/audio/sound/paper_relay.wav')} volume={0.7} />
      </Sequence>
      <Vignette strength={0.42} />
      <FilmGrain opacity={0.075} />
    </Canvas>
  );
};
