import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  OffthreadVideo,
  Sequence,
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

const authorityClipIn = 107;
const authoritySpokenDuration = 474;
const authorityRoomToneTail = 10;
const authorityDuration = authoritySpokenDuration + authorityRoomToneTail;

const Chronology: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const reveal = progress(frame, start + 12, start + 52, Easing.out(Easing.cubic));
  const one = progress(frame, start + 75, start + 122);
  const two = progress(frame, start + 230, start + 278);
  const three = progress(frame, start + 405, start + 452);
  const four = progress(frame, start + 560, start + 608);
  const nodes = [
    {x: 280, date: 'JUL 29', title: 'RATE HOLD', detail: '3.50–3.75% · 9–3 vote', opacity: one, color: cyan},
    {x: 720, date: 'AUG 7', title: 'JOBS + REVISIONS', detail: '−23K · May/June −103K', opacity: two, color: red},
    {x: 1160, date: 'AUG 12', title: 'JULY CPI', detail: '3.4% headline', opacity: three, color: copper},
    {x: 1600, date: 'AUG 14', title: 'RETAIL SALES', detail: 'arrived after the meeting', opacity: four, color: amber},
  ];
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 16), background: '#081115'}}>
      <div style={{position: 'absolute', right: -110, top: -150, width: 930, height: 1330, opacity: 0.055, transform: 'rotate(2deg)'}}>
        <Img src={staticFile('assets/documents/fed_transcript_page_01.png')} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
      </div>
      <ChapterSlug number={7} opacity={reveal}>No easy exit</ChapterSlug>
      <div style={{position: 'absolute', left: 98, top: 178, fontFamily: serif, fontSize: 83, lineHeight: 1.02}}>Put the dates<br />back in order.</div>
      <svg width="1920" height="1080" style={{position: 'absolute', inset: 0}}>
        <line x1="280" y1="610" x2="1600" y2="610" stroke="rgba(241,238,231,.2)" strokeWidth="3" />
        {nodes.map((node) => (
          <g key={node.date} opacity={node.opacity}>
            <circle cx={node.x} cy="610" r="16" fill={node.color} />
            <line x1={node.x} y1="610" x2={node.x} y2={node.x % 800 === 280 ? 515 : 705} stroke={node.color} strokeWidth="3" />
          </g>
        ))}
      </svg>
      {nodes.map((node, index) => {
        const top = index % 2 === 0 ? 430 : 700;
        return (
          <div key={node.date} style={{position: 'absolute', left: node.x - 130, top, width: 260, textAlign: 'center', opacity: node.opacity}}>
            <div style={{fontFamily: sans, fontSize: 18, fontWeight: 780, letterSpacing: '.14em', color: node.color}}>{node.date}</div>
            <div style={{fontFamily: sans, fontSize: 19, fontWeight: 700, marginTop: 10}}>{node.title}</div>
            <div style={{fontFamily: serif, fontSize: 21, color: silver, lineHeight: 1.25, marginTop: 7}}>{node.detail}</div>
          </div>
        );
      })}
      <div style={{position: 'absolute', left: 99, bottom: 74, width: 900, fontFamily: serif, fontSize: 33, lineHeight: 1.35, opacity: four}}>
        The July 29 assessment could not incorporate releases that did not yet exist.
      </div>
      <SourceTag>FEDERAL RESERVE / BLS / CENSUS · RELEASE CHRONOLOGY</SourceTag>
    </AbsoluteFill>
  );
};

const AuthorityMandate: React.FC = () => {
  const frame = useCurrentFrame();
  const fieldEnter = progress(frame, 4, 28, Easing.out(Easing.cubic));
  const portraitEnter = progress(frame, 12, 34, Easing.out(Easing.cubic));
  const recede = progress(frame, 404, 480, Easing.inOut(Easing.cubic));
  const pictureRelease = progress(frame, 462, authorityDuration, Easing.inOut(Easing.cubic));
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{background: `rgba(5,10,14,${fieldEnter})`}} />
      <div style={{position: 'absolute', inset: 0, opacity: fieldEnter, background: 'radial-gradient(circle at 50% 44%,rgba(35,48,72,.38),transparent 58%)'}} />
      <div style={{position: 'absolute', left: 82, top: 158, width: 460, opacity: fieldEnter}}>
        <div style={{fontFamily: sans, fontSize: 17, letterSpacing: '.16em', color: cyan}}>EMPLOYMENT</div>
        <div style={{height: 3, width: 370, marginTop: 18, background: cyan}} />
        <div style={{fontFamily: serif, fontSize: 38, lineHeight: 1.2, marginTop: 28, color: paper}}>Hiring weak.<br />Layoffs contained.</div>
      </div>
      <div style={{position: 'absolute', right: 82, top: 158, width: 460, textAlign: 'right', opacity: fieldEnter}}>
        <div style={{fontFamily: sans, fontSize: 17, letterSpacing: '.16em', color: copper}}>PRICES</div>
        <div style={{height: 3, width: 370, marginTop: 18, marginLeft: 'auto', background: copper}} />
        <div style={{fontFamily: serif, fontSize: 38, lineHeight: 1.2, marginTop: 28, color: paper}}>Headline inflation<br />still elevated.</div>
      </div>
      <div
        style={{
          position: 'absolute',
          left: 600 + recede * 60,
          top: 54 + recede * 154,
          width: 720 - recede * 120,
          height: 936 - recede * 236,
          opacity: portraitEnter * (1 - pictureRelease * 0.5),
          overflow: 'hidden',
          boxShadow: '0 30px 100px rgba(0,0,0,.55)',
        }}
      >
        <OffthreadVideo
          src={staticFile('assets/authority/fed_fomc_2026-07-29_clip02_dual_mandate_official_880x720_handles.mp4')}
          startFrom={authorityClipIn}
          endAt={authorityClipIn + authorityDuration}
          muted={false}
          volume={(f) => {
            const inLevel = progress(f, 0, 7, Easing.out(Easing.quad));
            const tailRelease = progress(
              f,
              authoritySpokenDuration + 6,
              authorityDuration,
              Easing.in(Easing.quad),
            );
            return inLevel * (1 - tailRelease);
          }}
          style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '62% 50%'}}
        />
        <div
          style={{
            position: 'absolute',
            left: 24,
            bottom: 24,
            padding: '12px 15px 11px',
            background: 'rgba(3,8,12,.76)',
            borderLeft: `3px solid ${cyan}`,
            opacity: 1 - pictureRelease,
          }}
        >
          <div style={{fontFamily: sans, fontSize: 17, fontWeight: 780, letterSpacing: '.12em', color: paper}}>KEVIN WARSH</div>
          <div style={{fontFamily: sans, fontSize: 13, marginTop: 5, letterSpacing: '.11em', color: silver}}>FEDERAL RESERVE CHAIRMAN · JULY 29, 2026</div>
        </div>
        <AbsoluteFill style={{boxShadow: 'inset 0 0 0 1px rgba(241,238,231,.12)'}} />
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 42, textAlign: 'center', fontFamily: sans, fontSize: 15, letterSpacing: '.1em', color: silver, opacity: fieldEnter * (1 - pictureRelease)}}>
        BOARD OF GOVERNORS OF THE FEDERAL RESERVE SYSTEM · FOMC PRESS CONFERENCE · JULY 29, 2026
      </div>
    </AbsoluteFill>
  );
};

const PolicyBind: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const split = progress(frame, start + 20, start + 92, Easing.inOut(Easing.cubic));
  const context = progress(frame, start + 135, start + 194);
  const noForecast = progress(frame, start + 285, start + 330);
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 16), background: paper, color: ink}}>
      <div style={{position: 'absolute', left: 102, top: 82, fontFamily: serif, fontSize: 67}}>The principle is simple. The policy choice is not.</div>
      <div style={{position: 'absolute', left: 102, top: 235, width: 790, height: 430, padding: '48px 52px', border: `2px solid ${cyan}`, transform: `translateX(${(1 - split) * -50}px)`, opacity: split}}>
        <div style={{fontFamily: sans, fontSize: 18, letterSpacing: '.15em', color: '#397F7B'}}>EMPLOYMENT RISK</div>
        <div style={{fontFamily: serif, fontSize: 58, lineHeight: 1.03, marginTop: 34}}>Hiring is weak enough<br />to matter.</div>
        <div style={{fontFamily: sans, fontSize: 24, fontWeight: 750, color: '#397F7B', marginTop: 54}}>LOW HIRE · LOW QUIT · LOW FIRE</div>
      </div>
      <div style={{position: 'absolute', right: 102, top: 235, width: 790, height: 430, padding: '48px 52px', border: `2px solid ${copper}`, transform: `translateX(${(1 - split) * 50}px)`, opacity: split}}>
        <div style={{fontFamily: sans, fontSize: 18, letterSpacing: '.15em', color: '#9C5638'}}>PRICE RISK</div>
        <div style={{fontFamily: serif, fontSize: 58, lineHeight: 1.03, marginTop: 34}}>3.4 percent resists<br />an automatic easing story.</div>
        <div style={{fontFamily: sans, fontSize: 24, fontWeight: 750, color: '#9C5638', marginTop: 54}}>HEADLINE CPI · JULY</div>
      </div>
      <div style={{position: 'absolute', left: 102, right: 102, bottom: 115, display: 'flex', justifyContent: 'center', gap: 86, opacity: context}}>
        <div style={{fontFamily: sans, fontSize: 27, color: '#334146'}}><b style={{fontSize: 54}}>+3.9%</b> private demand</div>
        <div style={{width: 1, height: 72, background: 'rgba(8,16,21,.24)'}} />
        <div style={{fontFamily: sans, fontSize: 27, color: '#334146'}}><b style={{fontSize: 54}}>+2.2%</b> productivity</div>
        <div style={{fontFamily: serif, fontSize: 28, width: 430, lineHeight: 1.25, color: '#4F5D61'}}>complicate both sides of the choice</div>
      </div>
      <div style={{position: 'absolute', right: 102, top: 102, fontFamily: sans, fontSize: 16, letterSpacing: '.13em', color: red, opacity: noForecast}}>NO RATE FORECAST · NO RECESSION DATE</div>
      <SourceTag color="#536267">OFFICIAL DATA THROUGH AUGUST 15, 2026</SourceTag>
    </AbsoluteFill>
  );
};

const NoForecastRoom: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const show = progress(frame, start + 18, start + 64);
  const wipe = progress(frame, start + 165, start + 228, Easing.inOut(Easing.cubic));
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 16), background: ink}}>
      <div style={{position: 'absolute', left: 98, top: 104, fontFamily: serif, fontSize: 76}}>The useful question is conditional.</div>
      <div style={{position: 'absolute', left: 101, top: 292, width: 1220, fontFamily: serif, fontSize: 57, lineHeight: 1.16, opacity: show}}>
        Not: <span style={{color: red}}>what happens next?</span><br />But: <span style={{color: cyan}}>what evidence would change the diagnosis?</span>
      </div>
      <div style={{position: 'absolute', left: 100, right: 100, bottom: 130, height: 5, background: `linear-gradient(90deg,${cyan} 0 ${wipe * 48}%,${paper} ${wipe * 48}% ${wipe * 67}%,${red} ${wipe * 67}% 100%)`, opacity: show}} />
      <div style={{position: 'absolute', left: 100, bottom: 77, fontFamily: sans, fontSize: 17, letterSpacing: '.14em', color: silver, opacity: show}}>THAW</div>
      <div style={{position: 'absolute', left: '48%', bottom: 77, fontFamily: sans, fontSize: 17, letterSpacing: '.14em', color: silver, opacity: show}}>FREEZE</div>
      <div style={{position: 'absolute', right: 100, bottom: 77, fontFamily: sans, fontSize: 17, letterSpacing: '.14em', color: silver, opacity: show}}>BREAK</div>
    </AbsoluteFill>
  );
};

const ThreeStates: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const local = frame - start;
  const third = (end - start) / 3;
  const state = Math.min(2, Math.floor(Math.max(0, local) / third));
  const within = (local - state * third) / third;
  const reveal = Math.min(1, Math.max(0, within * 2.8));
  const states = [
    {
      name: 'CONTINUED FREEZE',
      color: paper,
      title: 'Near-zero payrolls. Low hires and quits. Claims contained.',
      detail: 'Participation stays weak. Growth stays concentrated.',
    },
    {
      name: 'THAW',
      color: cyan,
      title: 'Broader payroll gains. Participation recovers.',
      detail: 'Hires and quits rise without more layoffs.',
    },
    {
      name: 'BREAK',
      color: red,
      title: 'Claims and layoffs jump.',
      detail: 'Unemployment rises alongside job loss.',
    },
  ];
  const current = states[state];
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 12), background: state === 2 ? '#150A0A' : state === 1 ? '#071615' : '#0A1115'}}>
      <div style={{position: 'absolute', inset: 0, opacity: 0.26}}>
        {Array.from({length: 16}).map((_, index) => {
          const x = 105 + index * 112;
          const height = state === 0 ? 240 : state === 1 ? 180 + (index % 5) * 45 : 150 + index * 34;
          return <div key={index} style={{position: 'absolute', left: x, bottom: 165, width: 4, height, background: current.color, transform: `scaleY(${reveal})`, transformOrigin: 'bottom'}} />;
        })}
      </div>
      <div style={{position: 'absolute', left: 105, top: 106, fontFamily: sans, fontSize: 19, fontWeight: 780, letterSpacing: '.18em', color: current.color, opacity: reveal}}>{current.name}</div>
      <div style={{position: 'absolute', left: 105, top: 230, width: 1320, opacity: reveal, transform: `translateY(${(1 - reveal) * 24}px)`}}>
        <div style={{fontFamily: serif, fontSize: 77, lineHeight: 1.04}}>{current.title}</div>
        <div style={{fontFamily: serif, fontSize: 42, color: silver, marginTop: 34}}>{current.detail}</div>
      </div>
      <div style={{position: 'absolute', right: 92, bottom: 66, fontFamily: sans, fontSize: 16, letterSpacing: '.14em', color: silver}}>THE THESIS IS TESTABLE</div>
    </AbsoluteFill>
  );
};

const EndingRoom: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const local = progress(frame, start, end);
  const show = progress(frame, start + 25, start + 78);
  const empty = progress(frame, start + 145, start + 235, Easing.inOut(Easing.cubic));
  const final = progress(frame, start + 245, start + 300);
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 12)}}>
      <FullBleedVideo src="assets/documentary/office_workers_pexels_6549254.mp4" startFrom={1020} muted style={{filter: `saturate(${0.5 - empty * 0.24}) brightness(${0.54 - empty * 0.12})`, transform: `scale(${1.04 + local * 0.055})`, opacity: 1 - empty}} />
      <AbsoluteFill style={{opacity: empty}}>
        <FullBleedVideo src="assets/documentary/empty_office_pexels_7844843.mp4" startFrom={100} muted style={{filter: 'saturate(.32) brightness(.42)', transform: `scale(${1.07 + local * 0.05})`}} />
      </AbsoluteFill>
      <AbsoluteFill style={{background: `linear-gradient(90deg,rgba(2,6,8,.88),rgba(2,6,8,${0.16 + empty * 0.48}) 67%,rgba(2,6,8,.58))`}} />
      <div style={{position: 'absolute', left: 103, top: 132, width: 1140, opacity: show * (1 - empty * 0.22)}}>
        <div style={{fontFamily: serif, fontSize: 72, lineHeight: 1.04}}>Fewer entrances. Fewer exits.<br />Fewer dismissals.</div>
      </div>
      <div style={{position: 'absolute', left: 103, bottom: 115, width: 1420, opacity: final}}>
        <div style={{fontFamily: serif, fontSize: 66, lineHeight: 1.08, letterSpacing: '-.03em'}}>The labor market has not broken.</div>
        <div style={{fontFamily: serif, fontSize: 66, lineHeight: 1.08, letterSpacing: '-.03em', color: copper}}>But it has less room to absorb whatever comes next.</div>
      </div>
    </AbsoluteFill>
  );
};

export const Chapter07: React.FC<ChapterProps> = ({durationInFrames}) => {
  const authorityStart = 997;
  const p1 = 997;
  const p2 = Math.round(durationInFrames * 0.47);
  const p3 = Math.round(durationInFrames * 0.61);
  const p4 = Math.round(durationInFrames * 0.81);
  return (
    <Canvas>
      <Chronology start={0} end={p1 + 18} />
      <Sequence from={authorityStart} durationInFrames={authorityDuration} premountFor={30}>
        <AuthorityMandate />
      </Sequence>
      <PolicyBind start={authorityStart + authoritySpokenDuration - 12} end={p2 + 18} />
      <NoForecastRoom start={p2 - 12} end={p3 + 15} />
      <ThreeStates start={p3 - 10} end={p4 + 15} />
      <EndingRoom start={p4 - 12} end={durationInFrames} />

      <Audio src={staticFile('assets/audio/narration/chapter_07.wav')} volume={1} />
      <Audio
        src={staticFile('assets/audio/sound/chapter_07_bed.m4a')}
        volume={(f) => {
          const down = progress(f, authorityStart - 38, authorityStart + 8);
          const up = progress(f, authorityStart + authorityDuration - 10, authorityStart + authorityDuration + 42);
          return 0.72 * (1 - down * (1 - up) * 0.96);
        }}
      />
      <Vignette strength={0.46} />
      <FilmGrain opacity={0.08} />
    </Canvas>
  );
};
