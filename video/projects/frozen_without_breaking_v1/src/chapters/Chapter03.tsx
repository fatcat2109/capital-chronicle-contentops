import React from 'react';
import {AbsoluteFill, Audio, Easing, staticFile, useCurrentFrame} from 'remotion';
import type {ChapterProps} from '../types';
import {
  Canvas,
  ChapterSlug,
  FilmGrain,
  FullBleedVideo,
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

const ThresholdMontage: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const span = Math.max(1, end - start);
  const phase = progress(frame, start, end);
  const officeTurn = progress(frame, start + span * 0.66, start + span * 0.73);
  const choose = phase < 0.7 ? 0 : 1;
  const assets = [
    'assets/documentary/commuters_subway_cc0_pexels_855749.mp4',
    'assets/documentary/office_workers_pexels_6549254.mp4',
  ];
  const show = progress(frame, start + 12, start + 48, Easing.out(Easing.cubic));
  const narrow = progress(frame, start + span * 0.38, end - 34, Easing.inOut(Easing.cubic));
  const railHint = progress(frame, end - 116, end - 42);

  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 16), background: '#050C10'}}>
      <FullBleedVideo
        key={assets[choose]}
        src={assets[choose]}
        startFrom={choose === 0 ? 34 : 660}
        muted
        style={{
          filter: `saturate(${0.68 - officeTurn * 0.16}) brightness(${0.68 - officeTurn * 0.1}) contrast(1.08)`,
          transform: `scale(${1.035 + phase * 0.035})`,
        }}
      />
      <AbsoluteFill style={{background: 'linear-gradient(90deg,rgba(3,8,11,.9),rgba(3,8,11,.1) 62%,rgba(3,8,11,.7))'}} />
      <div style={{position: 'absolute', inset: 0, borderLeft: `${Math.round(narrow * 118)}px solid rgba(3,8,11,.58)`, borderRight: `${Math.round(narrow * 118)}px solid rgba(3,8,11,.58)`}} />
      <ChapterSlug number={3} opacity={show}>The revolving door stopped</ChapterSlug>
      <div style={{position: 'absolute', left: 98, bottom: 132, width: 1070, opacity: show}}>
        <div style={{fontFamily: serif, fontSize: 92, lineHeight: 0.98, letterSpacing: '-.045em'}}>
          Count the movement,<br /><span style={{color: copper}}>not just the jobs.</span>
        </div>
      </div>
      <div style={{position: 'absolute', right: 70 + narrow * 130, top: 130, bottom: 130, width: 3, background: `linear-gradient(${cyan},transparent)`, opacity: 0.45}} />
      <div style={{position: 'absolute', right: 92, bottom: 62, fontFamily: sans, fontSize: 13, letterSpacing: '.14em', color: silver, opacity: show}}>
        ILLUSTRATIVE THRESHOLD · {choose === 0 ? 'STATION' : 'OFFICE'}
      </div>
      <div style={{position: 'absolute', left: 98, right: 98, top: 222, display: 'flex', gap: 8, opacity: railHint}}>
        {['HIRING', 'QUITTING', 'LAYOFFS'].map((label, index) => (
          <div key={label} style={{height: 3, flex: 1, background: index === 0 ? cyan : index === 1 ? copper : silver}}>
            <div style={{marginTop: 12, fontFamily: sans, fontSize: 12, letterSpacing: '.14em', color: silver}}>{label}</div>
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

const FlowRails: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const span = Math.max(1, end - start);
  const hire = progress(frame, start + span * 0.04, start + span * 0.22, Easing.out(Easing.cubic));
  const quit = progress(frame, start + span * 0.62, start + span * 0.73, Easing.out(Easing.cubic));
  const fire = progress(frame, start + span * 0.8, start + span * 0.89, Easing.out(Easing.cubic));
  const unified = progress(frame, start + span * 0.91, start + span * 0.975, Easing.inOut(Easing.cubic));
  const hireContextOut = progress(frame, start + span * 0.31, start + span * 0.42);
  const rails = [
    {name: 'HIRE', before: '3.9%', now: '3.4%', level: '5.348M HIRES', y: 350, color: cyan, wave: 24, stage: hire},
    {name: 'QUIT', before: '2.3%', now: '2.0%', level: '3.232M QUITS', y: 570, color: copper, wave: 18, stage: quit},
    {name: 'LAYOFF / DISCHARGE', before: '1.3%', now: '1.1%', level: '1.766M LAYOFFS / DISCHARGES', y: 790, color: silver, wave: 12, stage: fire},
  ];

  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 18), background: '#081115'}}>
      <div style={{position: 'absolute', left: 100, top: 72, fontFamily: serif, fontSize: 68, opacity: hire * (1 - quit)}}>First rail: hiring.</div>
      <div style={{position: 'absolute', left: 100, top: 72, fontFamily: serif, fontSize: 68, opacity: quit * (1 - fire)}}>Second rail: quitting.</div>
      <div style={{position: 'absolute', left: 100, top: 72, fontFamily: serif, fontSize: 68, opacity: fire}}>All three rails ended lower.</div>
      <div style={{position: 'absolute', right: 98, top: 92, fontFamily: sans, fontSize: 17, letterSpacing: '.14em', color: silver}}>FEB 2020 → JUN 2026</div>

      <div style={{position: 'absolute', left: 102, top: 187, display: 'flex', alignItems: 'baseline', gap: 18, opacity: hire * (1 - hireContextOut)}}>
        <span style={{fontFamily: sans, fontSize: 28, fontWeight: 760, color: silver}}>7.359M OPENINGS</span>
        <span style={{fontFamily: serif, fontSize: 29, color: copper}}>but</span>
        <span style={{fontFamily: sans, fontSize: 28, fontWeight: 760, color: cyan}}>5.348M HIRES</span>
      </div>

      <svg width="1920" height="1080" style={{position: 'absolute', inset: 0}}>
        <line x1="270" y1="262" x2="270" y2="878" stroke="rgba(241,238,231,.14)" />
        <line x1="1640" y1="262" x2="1640" y2="878" stroke="rgba(241,238,231,.14)" />
        {rails.map((rail, index) => {
          const y2 = rail.y + 55;
          const d = `M 270 ${rail.y} C 520 ${rail.y - rail.wave}, 720 ${rail.y + rail.wave}, 960 ${rail.y + 12} S 1370 ${rail.y + 30}, 1640 ${y2}`;
          return (
            <g key={rail.name}>
              <path d={d} fill="none" stroke="rgba(241,238,231,.09)" strokeWidth="3" strokeDasharray="7 12" />
              <path d={d} fill="none" stroke={rail.color} strokeWidth={index === 0 ? 8 : 6} strokeLinecap="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - rail.stage} />
              <circle cx="270" cy={rail.y} r="8" fill={rail.color} opacity={rail.stage} />
              <circle cx="1640" cy={y2} r="11" fill={rail.color} opacity={rail.stage} />
            </g>
          );
        })}
        <path d="M 1648 397 L 1668 397 L 1668 845 L 1648 845" fill="none" stroke={copper} strokeWidth="3" opacity={unified} />
      </svg>

      {rails.map((rail) => (
        <React.Fragment key={rail.name}>
          <div style={{position: 'absolute', left: 92, top: rail.y - 34, width: 150, textAlign: 'right', opacity: rail.stage}}>
            <div style={{fontFamily: sans, fontSize: 38, fontWeight: 760, color: rail.color}}>{rail.before}</div>
            <div style={{fontFamily: sans, fontSize: 13, letterSpacing: '.12em', color: silver}}>FEB 2020</div>
          </div>
          <div style={{position: 'absolute', left: 1682, top: rail.y + 8, width: 214, opacity: rail.stage}}>
            <div style={{fontFamily: sans, fontSize: 55, fontWeight: 800, color: rail.color}}>{rail.now}</div>
            <div style={{fontFamily: sans, fontSize: 14, letterSpacing: '.12em', color: silver}}>{rail.name} RATE · JUNE</div>
            <div style={{fontFamily: sans, fontSize: 11, lineHeight: 1.3, marginTop: 7, letterSpacing: '.07em', color: rail.color, opacity: 0.78}}>{rail.level}</div>
          </div>
        </React.Fragment>
      ))}

      <div style={{position: 'absolute', left: 470, right: 470, top: 914, textAlign: 'center', opacity: unified, transform: `translateY(${(1 - unified) * 20}px)`}}>
        <div style={{fontFamily: sans, fontSize: 14, letterSpacing: '.16em', color: copper}}>THE COMBINED DIAGNOSIS IS NOW EARNED</div>
        <div style={{fontFamily: serif, fontSize: 35, lineHeight: 1.12, marginTop: 8}}>Three slower flows. One low-motion market.</div>
      </div>
      <SourceTag>BLS JOLTS · JUNE 2026 · SEASONALLY ADJUSTED LEVELS / RATES</SourceTag>
    </AbsoluteFill>
  );
};

const MatchingMap: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const span = Math.max(1, end - start);
  const appear = progress(frame, start + 14, start + 58, Easing.out(Easing.cubic));
  const mismatch = progress(frame, start + span * 0.22, start + span * 0.36, Easing.inOut(Easing.cubic));
  const threshold = progress(frame, start + span * 0.76, start + span * 0.84, Easing.inOut(Easing.cubic));
  const ratioScale = 1 - mismatch * 0.45;
  const frictions = [
    {label: 'PLACE', detail: 'wrong location', color: cyan},
    {label: 'SKILL', detail: 'different requirement', color: copper},
    {label: 'PAY', detail: 'wrong offer', color: copper},
    {label: 'NO HIRE', detail: 'opening never converts', color: red},
  ];

  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 16), background: paper, color: ink}}>
      <AbsoluteFill style={{background: 'radial-gradient(circle at 50% 48%,rgba(255,255,255,.8),rgba(220,214,201,.42) 72%,rgba(187,177,157,.36))'}} />
      <div style={{position: 'absolute', left: 104, top: 82, fontFamily: serif, fontSize: 66}}>
        <span style={{opacity: 1 - mismatch}}>At a distance: apparent balance.</span>
        <span style={{position: 'absolute', left: 0, top: 0, width: 1200, opacity: mismatch}}>A ratio is a map. Not a match.</span>
      </div>

      <div
        style={{
          position: 'absolute',
          left: 104,
          top: 194,
          display: 'flex',
          alignItems: 'baseline',
          gap: 24,
          opacity: appear,
          transform: `translate(${-mismatch * 8}px, ${-mismatch * 38}px) scale(${ratioScale})`,
          transformOrigin: 'left top',
        }}
      >
        <div style={{fontFamily: sans, fontSize: 166, fontWeight: 820, letterSpacing: '-.075em'}}>1.04</div>
        <div style={{fontFamily: serif, fontSize: 34, lineHeight: 1.25}}>opening<br />per unemployed person</div>
      </div>

      <div style={{position: 'absolute', left: 470, right: 470, top: 500, height: 220, opacity: appear * (1 - mismatch * 0.65)}}>
        <div style={{position: 'absolute', left: 160 - mismatch * 168, top: 35, width: 170, height: 170, borderRadius: '50%', border: `4px solid ${cyan}`, background: 'rgba(37,174,178,.08)'}} />
        <div style={{position: 'absolute', right: 160 - mismatch * 168, top: 35, width: 170, height: 170, borderRadius: '50%', border: `4px solid ${copper}`, background: 'rgba(184,109,70,.08)'}} />
        <div style={{position: 'absolute', left: 274, right: 274, top: 118, height: 2, background: ink, opacity: 0.25 * (1 - mismatch)}} />
        <div style={{position: 'absolute', left: 111 - mismatch * 168, top: 222, width: 270, textAlign: 'center', fontFamily: sans, fontSize: 13, letterSpacing: '.14em'}}>UNEMPLOYED PEOPLE</div>
        <div style={{position: 'absolute', right: 111 - mismatch * 168, top: 222, width: 270, textAlign: 'center', fontFamily: sans, fontSize: 13, letterSpacing: '.14em'}}>JOB OPENINGS</div>
      </div>

      <div style={{position: 'absolute', left: 108, right: 108, top: 500, display: 'flex', gap: 24, opacity: mismatch}}>
        {frictions.map((friction, index) => {
          const reveal = progress(frame, start + span * (0.34 + index * 0.075), start + span * (0.42 + index * 0.075), Easing.out(Easing.cubic));
          return (
            <div key={friction.label} style={{position: 'relative', flex: 1, height: 255, borderTop: `5px solid ${friction.color}`, borderBottom: '1px solid rgba(8,16,21,.22)', opacity: reveal, transform: `translateY(${(1 - reveal) * 42}px)`}}>
              <div style={{fontFamily: sans, fontSize: 17, fontWeight: 780, letterSpacing: '.15em', marginTop: 24, color: friction.color}}>{friction.label}</div>
              <div style={{fontFamily: serif, fontSize: 35, lineHeight: 1.08, marginTop: 72}}>{friction.detail}</div>
              <div style={{position: 'absolute', right: 16, top: 68, width: 72 - reveal * 44, height: 72, border: `3px solid ${friction.color}`, opacity: 0.65}} />
            </div>
          );
        })}
      </div>
      <div style={{position: 'absolute', left: 110, bottom: 126, fontFamily: sans, fontSize: 18, fontWeight: 720, letterSpacing: '.13em', color: red, opacity: mismatch * (1 - threshold)}}>
        AN OPENING IS NOT A COMPLETED HIRE
      </div>

      <AbsoluteFill style={{opacity: threshold}}>
        <FullBleedVideo
          src="assets/documentary/job_interview_pexels_5438891.mp4"
          startFrom={80}
          muted
          style={{filter: 'saturate(.48) brightness(.62) contrast(1.08)', transform: `scale(${1.04 + threshold * 0.035}) translateX(${threshold * 18}px)`}}
        />
        <AbsoluteFill style={{background: 'linear-gradient(90deg,rgba(3,8,11,.94),rgba(3,8,11,.62) 52%,rgba(3,8,11,.16))'}} />
        <div style={{position: 'absolute', left: 104, top: 160, width: 830, opacity: progress(frame, start + span * 0.8, start + span * 0.9)}}>
          <div style={{fontFamily: sans, fontSize: 17, letterSpacing: '.16em', color: cyan}}>FROM A DISTANCE · 1.04</div>
          <div style={{fontFamily: serif, fontSize: 78, lineHeight: 1.02, marginTop: 22}}>Balanced on paper.</div>
          <div style={{fontFamily: serif, fontSize: 78, lineHeight: 1.02, color: copper}}>Narrow at the door.</div>
        </div>
        <div style={{position: 'absolute', right: 92, bottom: 62, fontFamily: sans, fontSize: 13, letterSpacing: '.14em', color: silver}}>ILLUSTRATIVE THRESHOLD · INTERVIEW</div>
      </AbsoluteFill>

      <AbsoluteFill style={{opacity: 1 - threshold, pointerEvents: 'none'}}>
        <SourceTag color="#536267">BLS JOLTS / HOUSEHOLD SURVEY · JUNE 2026</SourceTag>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const ClaimsCalm: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const span = Math.max(1, end - start);
  const draw = progress(frame, start + 18, start + span * 0.24, Easing.out(Easing.cubic));
  const value = progress(frame, start + span * 0.13, start + span * 0.25, Easing.out(Easing.cubic));
  const compare = progress(frame, start + span * 0.27, start + span * 0.39);
  const calm = progress(frame, start + span * 0.37, start + span * 0.49);
  const long = progress(frame, start + span * 0.57, start + span * 0.68, Easing.inOut(Easing.cubic));
  const counterpoint = progress(frame, start + span * 0.7, start + span * 0.8);
  const claimsOpacity = 1 - long * 0.76;

  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 16), background: '#0A1317'}}>
      <div style={{position: 'absolute', left: 102, top: 84, fontFamily: serif, fontSize: 69, opacity: 1 - long}}>The trapdoor has not opened.</div>
      <div style={{position: 'absolute', left: 102, top: 84, fontFamily: serif, fontSize: 69, opacity: long}}>Low firing can coexist with a long wait.</div>

      <div style={{opacity: claimsOpacity}}>
        <svg width="1920" height="1080" style={{position: 'absolute', inset: 0}}>
          <line x1="130" y1="658" x2="1770" y2="658" stroke="rgba(241,238,231,.13)" />
          <path d="M 150 640 C 290 590 390 670 540 622 S 790 652 920 620 S 1190 674 1330 628 S 1570 644 1760 615" fill="none" stroke={cyan} strokeWidth="6" strokeLinecap="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - draw} />
          <line x1="1510" y1="615" x2="1510" y2="735" stroke={cyan} strokeWidth="2" opacity={value} />
          <circle cx="1510" cy="615" r="10" fill={cyan} opacity={value} />
        </svg>
        <div style={{position: 'absolute', left: 105, top: 292, opacity: value, transform: `translateY(${(1 - value) * 26}px)`}}>
          <div style={{fontFamily: sans, fontSize: 150, fontWeight: 820, letterSpacing: '-.07em', color: cyan}}>209K</div>
          <div style={{fontFamily: sans, fontSize: 19, letterSpacing: '.14em', color: silver}}>INITIAL CLAIMS · WEEK ENDING AUGUST 8</div>
        </div>
        <div style={{position: 'absolute', left: 107, top: 505, fontFamily: sans, fontSize: 16, color: silver, lineHeight: 1.5, opacity: compare}}>
          <span style={{color: paper, fontWeight: 760}}>224K</span> · comparable 2025 week<br />
          Continued claims were lower year over year too.
        </div>
        <div style={{position: 'absolute', right: 108, top: 290, width: 500, opacity: calm, transform: `translateX(${(1 - calm) * 32}px)`}}>
          <div style={{fontFamily: serif, fontSize: 50, lineHeight: 1.08}}>No broad insured-layoff wave.</div>
          <div style={{fontFamily: sans, fontSize: 17, letterSpacing: '.12em', color: cyan, marginTop: 22}}>CLAIMS FLOW · CONTAINED</div>
        </div>
      </div>

      <div style={{position: 'absolute', left: 104, right: 104, top: 255, bottom: 104, opacity: long}}>
        <div style={{position: 'absolute', left: 0, top: 96, width: 580}}>
          <div style={{fontFamily: sans, fontSize: 14, letterSpacing: '.15em', color: cyan}}>CURRENT INITIAL-CLAIMS FLOW</div>
          <div style={{fontFamily: sans, fontSize: 78, fontWeight: 820, color: cyan, marginTop: 12}}>209K</div>
          <div style={{fontFamily: serif, fontSize: 30, lineHeight: 1.25, color: silver}}>No broad wave<br />in new claims.</div>
        </div>
        <div style={{position: 'absolute', left: 710, top: 34, bottom: 30, width: 2, background: 'rgba(241,238,231,.18)'}} />
        <div style={{position: 'absolute', left: 820, top: 28, right: 0, opacity: counterpoint, transform: `translateX(${(1 - counterpoint) * 38}px)`}}>
          <div style={{fontFamily: sans, fontSize: 14, letterSpacing: '.15em', color: copper}}>DURATION INSIDE UNEMPLOYMENT · JULY</div>
          <div style={{display: 'flex', alignItems: 'baseline', gap: 26, marginTop: 4}}>
            <span style={{fontFamily: sans, fontSize: 148, fontWeight: 830, letterSpacing: '-.07em', color: copper}}>25.5%</span>
            <span style={{fontFamily: serif, fontSize: 36, lineHeight: 1.05}}>≈ 1 in 4</span>
          </div>
          <div style={{fontFamily: serif, fontSize: 38, lineHeight: 1.18, marginTop: 8}}>unemployed for at least<br /><span style={{color: copper}}>27 weeks</span></div>
          <div style={{fontFamily: sans, fontSize: 14, letterSpacing: '.12em', color: silver, marginTop: 25}}>1.771M PEOPLE · SEASONALLY ADJUSTED</div>
        </div>
        <div style={{position: 'absolute', left: 820, bottom: 20, width: 830, fontFamily: sans, fontSize: 17, letterSpacing: '.12em', color: silver, opacity: counterpoint}}>
          WEAK ENTRY CAN HURT WITHOUT A FIRING SPIKE
        </div>
      </div>
      <SourceTag>DOL CLAIMS · AUG 8 / BLS CPS · JULY 2026</SourceTag>
    </AbsoluteFill>
  );
};

const HumanThresholds: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const span = Math.max(1, end - start);
  const phase = progress(frame, start, end);
  const choose = phase < 0.36 ? 0 : phase < 0.68 ? 1 : 2;
  const assets = [
    'assets/documentary/office_workers_pexels_6549254.mp4',
    'assets/documentary/job_interview_pexels_5438891.mp4',
    'assets/documentary/commuters_subway_cc0_pexels_855749.mp4',
  ];
  const diagnosis = progress(frame, start + 12, start + 54) * (1 - progress(frame, start + span * 0.22, start + span * 0.3));
  const stable = progress(frame, start + span * 0.1, start + span * 0.18) * (1 - progress(frame, start + span * 0.33, start + span * 0.4));
  const closed = progress(frame, start + span * 0.39, start + span * 0.46) * (1 - progress(frame, start + span * 0.62, start + span * 0.68));
  const trap = progress(frame, start + span * 0.69, start + span * 0.74) * (1 - progress(frame, start + span * 0.8, start + span * 0.84));
  const stopped = progress(frame, start + span * 0.79, start + span * 0.84) * (1 - progress(frame, start + span * 0.91, start + span * 0.95));
  const handoff = progress(frame, start + span * 0.9, start + span * 0.955);
  const startFrom = choose === 0 ? 690 : choose === 1 ? 80 : 32;

  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 14), background: '#050B0E'}}>
      <FullBleedVideo
        key={assets[choose]}
        src={assets[choose]}
        startFrom={startFrom}
        muted
        style={{filter: 'saturate(.48) brightness(.56) contrast(1.08)', transform: `scale(${1.045 + phase * 0.045}) translateX(${choose === 1 ? 18 : -phase * 18}px)`}}
      />
      <AbsoluteFill style={{background: choose === 1 ? 'linear-gradient(90deg,rgba(3,8,11,.92),rgba(3,8,11,.38) 62%,rgba(3,8,11,.7))' : 'linear-gradient(90deg,rgba(3,8,11,.9),rgba(3,8,11,.2) 62%,rgba(3,8,11,.68))'}} />

      <div style={{position: 'absolute', left: 102, right: 102, top: 78, display: 'flex', alignItems: 'center', gap: 28, opacity: diagnosis}}>
        {['LOW HIRE', 'LOW QUIT', 'LOW FIRE'].map((label, index) => (
          <React.Fragment key={label}>
            {index > 0 ? <div style={{width: 52, height: 2, background: copper}} /> : null}
            <div style={{fontFamily: sans, fontSize: 24, fontWeight: 770, letterSpacing: '.18em', color: index === 0 ? cyan : index === 1 ? copper : paper}}>{label}</div>
          </React.Fragment>
        ))}
      </div>

      <div style={{position: 'absolute', left: 104, top: 230, width: 1060, opacity: stable}}>
        <div style={{fontFamily: serif, fontSize: 88, lineHeight: 1.01, letterSpacing: '-.04em'}}>Stable if you are inside.</div>
        <div style={{fontFamily: sans, fontSize: 16, letterSpacing: '.15em', color: cyan, marginTop: 24}}>LOW FIRING · INCUMBENT VIEW</div>
      </div>

      <div style={{position: 'absolute', left: 104, top: 190, width: 1120, opacity: closed}}>
        <div style={{fontFamily: serif, fontSize: 86, lineHeight: 1.02, letterSpacing: '-.04em', color: copper}}>Closed if you are trying to enter.</div>
        <div style={{fontFamily: sans, fontSize: 17, letterSpacing: '.15em', color: silver, marginTop: 28}}>ENTER · RE-ENTER · TRADE UP</div>
      </div>

      <div style={{position: 'absolute', left: 104, top: 215, width: 1060, opacity: trap}}>
        <div style={{fontFamily: serif, fontSize: 82, lineHeight: 1.02}}>The trapdoor has not opened.</div>
      </div>
      <div style={{position: 'absolute', left: 104, top: 215, width: 1120, opacity: stopped}}>
        <div style={{fontFamily: serif, fontSize: 82, lineHeight: 1.02}}>The revolving door has<br /><span style={{color: copper}}>nearly stopped.</span></div>
      </div>

      <div style={{position: 'absolute', left: 104, right: 104, bottom: 110, paddingTop: 24, borderTop: `2px solid ${copper}`, opacity: handoff, transform: `translateY(${(1 - handoff) * 24}px)`}}>
        <div style={{fontFamily: sans, fontSize: 14, letterSpacing: '.17em', color: cyan}}>NEXT · THE SOURCE OF THE REMAINING GROWTH</div>
        <div style={{fontFamily: serif, fontSize: 50, lineHeight: 1.08, marginTop: 13}}>Where is the remaining job growth coming from?</div>
      </div>
      <div style={{position: 'absolute', right: 92, bottom: 62, fontFamily: sans, fontSize: 13, letterSpacing: '.14em', color: silver}}>
        ILLUSTRATIVE THRESHOLD · {choose === 0 ? 'OFFICE' : choose === 1 ? 'INTERVIEW' : 'STATION'}
      </div>
    </AbsoluteFill>
  );
};

export const Chapter03: React.FC<ChapterProps> = ({durationInFrames}) => {
  const thresholdEnd = Math.round(durationInFrames * 0.13);
  const railsStart = Math.round(durationInFrames * 0.105);
  const railsEnd = Math.round(durationInFrames * 0.665);
  const matchingStart = Math.round(durationInFrames * 0.215);
  const matchingEnd = Math.round(durationInFrames * 0.48);
  const claimsStart = Math.round(durationInFrames * 0.64);
  const claimsEnd = Math.round(durationInFrames * 0.86);
  const humanStart = Math.round(durationInFrames * 0.835);

  return (
    <Canvas>
      <ThresholdMontage start={0} end={thresholdEnd + 15} />
      <FlowRails start={railsStart} end={railsEnd} />
      <MatchingMap start={matchingStart} end={matchingEnd} />
      <ClaimsCalm start={claimsStart} end={claimsEnd} />
      <HumanThresholds start={humanStart} end={durationInFrames} />
      <Audio src={staticFile('assets/audio/narration/chapter_03.wav')} volume={1} />
      <Audio src={staticFile('assets/audio/sound/chapter_03_bed.m4a')} volume={0.82} />
      <Vignette strength={0.48} />
      <FilmGrain opacity={0.085} />
    </Canvas>
  );
};
