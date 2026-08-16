import React from 'react';
import {AbsoluteFill, Audio, Easing, interpolate, staticFile, useCurrentFrame} from 'remotion';
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

const SurveyGrammar: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const enter = progress(frame, start + 6, start + 42, Easing.out(Easing.cubic));
  const roster = progress(frame, start + 54, start + 94, Easing.out(Easing.cubic));
  const firstJob = progress(frame, start + 88, start + 126, Easing.out(Easing.cubic));
  const secondJob = progress(frame, start + 132, start + 174, Easing.out(Easing.cubic));
  const duplicate = progress(frame, start + 182, start + 226, Easing.inOut(Easing.cubic));
  const household = progress(frame, start + 234, start + 278, Easing.out(Easing.cubic));
  const classify = progress(frame, start + 286, start + 334, Easing.inOut(Easing.cubic));
  const clearExamples = progress(frame, end - 116, end - 78, Easing.in(Easing.cubic));
  const handoff = progress(frame, end - 70, end - 30, Easing.out(Easing.cubic));
  const exampleOpacity = enter * (1 - clearExamples);
  const rosterRows = [
    {employer: 'NORTHLINE CAFÉ', person: 'ALEX MORGAN', job: 'WEEKEND SHIFT', reveal: firstJob},
    {employer: 'CIVIC ARTS CENTER', person: 'ALEX MORGAN', job: 'EVENING SHIFT', reveal: secondJob},
  ];
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 18), background: ink}}>
      <div style={{opacity: exampleOpacity, transform: `translateY(${-22 * clearExamples}px) scale(${1 - clearExamples * 0.018})`}}>
        <ChapterSlug number={2} opacity={enter}>The rate that fell without hiring</ChapterSlug>
        <div style={{position: 'absolute', left: 104, right: 104, top: 174}}>
          <div style={{display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', borderBottom: '1px solid rgba(241,238,231,.18)', paddingBottom: 22}}>
            <div>
              <div style={{fontFamily: sans, fontSize: 18, letterSpacing: '.18em', color: copper}}>ESTABLISHMENT SURVEY</div>
              <div style={{fontFamily: serif, fontSize: 66, lineHeight: 1, marginTop: 16}}>A payroll job is the unit.</div>
            </div>
            <div style={{fontFamily: sans, fontSize: 15, letterSpacing: '.13em', color: silver}}>ILLUSTRATIVE UNIT EXAMPLE · NOT JULY ESTIMATES</div>
          </div>

          <div style={{position: 'absolute', left: 0, top: 160, width: 1040, height: 492, border: '1px solid rgba(241,238,231,.18)', background: 'rgba(241,238,231,.025)', opacity: roster, transform: `translateY(${(1 - roster) * 22}px)`}}>
            <div style={{height: 66, display: 'grid', gridTemplateColumns: '1.05fr 1.05fr .9fr', alignItems: 'center', padding: '0 34px', borderBottom: '1px solid rgba(241,238,231,.16)', fontFamily: sans, fontSize: 14, letterSpacing: '.16em', color: silver}}>
              <div>EMPLOYER</div>
              <div>PERSON ON PAYROLL</div>
              <div>JOB</div>
            </div>
            {rosterRows.map((row, index) => (
              <div
                key={row.employer}
                style={{
                  height: 126,
                  display: 'grid',
                  gridTemplateColumns: '1.05fr 1.05fr .9fr',
                  alignItems: 'center',
                  padding: '0 34px',
                  borderBottom: '1px solid rgba(241,238,231,.12)',
                  opacity: row.reveal,
                  transform: `translateX(${(1 - row.reveal) * -26}px)`,
                  background: index === 1 ? `rgba(202,124,82,${0.055 * duplicate})` : 'transparent',
                }}
              >
                <div style={{fontFamily: sans, fontSize: 21, letterSpacing: '.06em', color: paper}}>{row.employer}</div>
                <div style={{fontFamily: sans, fontSize: 30, fontWeight: 720, color: index === 1 ? copper : paper}}>{row.person}</div>
                <div style={{fontFamily: sans, fontSize: 17, letterSpacing: '.1em', color: silver}}>{row.job}</div>
              </div>
            ))}
            <div style={{position: 'absolute', left: 34, right: 34, bottom: 28, display: 'flex', alignItems: 'center', justifyContent: 'space-between', opacity: duplicate}}>
              <div style={{fontFamily: serif, fontSize: 30, color: silver}}>Same illustrative person, held on two employer payrolls.</div>
              <div style={{border: `1px solid ${copper}`, padding: '14px 22px 12px', fontFamily: sans, fontSize: 22, fontWeight: 760, letterSpacing: '.12em', color: copper}}>2 JOB ROWS</div>
            </div>
          </div>

          <div style={{position: 'absolute', right: 0, top: 160, width: 612, height: 492, border: `1px solid rgba(74,184,178,${0.42 * household})`, background: 'rgba(13,31,35,.86)', opacity: household, transform: `translateY(${(1 - household) * 22}px)`}}>
            <div style={{height: 66, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 30px', borderBottom: '1px solid rgba(241,238,231,.14)'}}>
              <div style={{fontFamily: sans, fontSize: 14, letterSpacing: '.16em', color: cyan}}>HOUSEHOLD RECORD</div>
              <div style={{fontFamily: sans, fontSize: 13, letterSpacing: '.12em', color: silver}}>ONE PERSON</div>
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: 24, padding: '30px 30px 22px'}}>
              <div style={{width: 96, height: 96, borderRadius: '50%', border: `2px solid ${cyan}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: serif, fontSize: 36, color: cyan}}>AM</div>
              <div>
                <div style={{fontFamily: sans, fontSize: 31, fontWeight: 720, color: paper}}>ALEX MORGAN</div>
                <div style={{fontFamily: sans, fontSize: 15, letterSpacing: '.11em', color: silver, marginTop: 8}}>REPORTS TWO PAYROLL JOBS</div>
              </div>
            </div>
            <div style={{margin: '0 30px', padding: '24px 0', borderTop: '1px solid rgba(241,238,231,.14)', borderBottom: '1px solid rgba(241,238,231,.14)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', opacity: classify}}>
              <div>
                <div style={{fontFamily: sans, fontSize: 14, letterSpacing: '.14em', color: silver}}>PERSON CLASSIFICATION</div>
                <div style={{fontFamily: serif, fontSize: 44, color: paper, marginTop: 4}}>Employed</div>
              </div>
              <div style={{width: 118, height: 118, borderRadius: '50%', border: `2px solid ${cyan}`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: cyan, transform: `scale(${0.82 + classify * 0.18})`}}>
                <div style={{fontFamily: sans, fontSize: 47, fontWeight: 800, lineHeight: .9}}>1</div>
                <div style={{fontFamily: sans, fontSize: 12, letterSpacing: '.13em', marginTop: 8}}>PERSON</div>
              </div>
            </div>
            <div style={{padding: '24px 30px', fontFamily: sans, fontSize: 18, letterSpacing: '.11em', color: cyan, opacity: classify}}>CLASSIFIED ONCE · EVEN WITH TWO JOBS</div>
          </div>
        </div>
      </div>

      <div style={{position: 'absolute', inset: 0, opacity: handoff}}>
        <div style={{position: 'absolute', left: 959, top: 164, bottom: 150, width: 2, background: cyan, transform: `scaleY(${handoff})`, transformOrigin: 'center'}} />
        <div style={{position: 'absolute', left: 0, right: 0, top: 394, textAlign: 'center', transform: `translateY(${(1 - handoff) * 18}px)`}}>
          <div style={{fontFamily: sans, fontSize: 16, letterSpacing: '.2em', color: silver}}>THE UNIT CHANGES</div>
          <div style={{fontFamily: serif, fontSize: 62, lineHeight: 1.02, margin: '20px auto 0', maxWidth: 1320, color: paper}}>
            <span style={{display: 'block'}}>Now hold one person</span>
            <span style={{display: 'block'}}>to one classification.</span>
          </div>
          <div style={{fontFamily: sans, fontSize: 19, letterSpacing: '.16em', color: cyan, marginTop: 28}}>JULY · HOUSEHOLD SURVEY →</div>
        </div>
      </div>
      <SourceTag>BLS · ESTABLISHMENT SURVEY / HOUSEHOLD SURVEY</SourceTag>
    </AbsoluteFill>
  );
};

const ParadoxRoom: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const local = progress(frame, start, end);
  const reveal = progress(frame, start + 12, start + 52);
  const move = progress(frame, start + 110, start + 250, Easing.inOut(Easing.cubic));
  const rate = progress(frame, start + 250, start + 300);
  const items = [
    {label: 'EMPLOYMENT', value: '−87K', color: paper, x: -360, y: -110},
    {label: 'LABOR FORCE', value: '−264K', color: copper, x: -500, y: 72},
    {label: 'UNEMPLOYED', value: '−178K', color: cyan, x: 440, y: -80},
    {label: 'OUTSIDE LABOR FORCE', value: '+381K', color: silver, x: 560, y: 115},
  ];
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 18)}}>
      <FullBleedVideo src="assets/documentary/empty_office_pexels_7844843.mp4" muted style={{filter: 'saturate(.62) brightness(.58) contrast(1.08)', transform: `scale(${1.06 + local * 0.06})`}} />
      <AbsoluteFill style={{background: 'linear-gradient(90deg,rgba(4,10,13,.82),rgba(4,10,13,.18) 54%,rgba(4,10,13,.74))'}} />
      <div style={{position: 'absolute', left: 944, top: 50, bottom: 50, width: 2, background: `rgba(241,238,231,${0.22 * reveal})`}} />
      <div style={{position: 'absolute', left: 836, top: 74, fontFamily: sans, fontSize: 16, letterSpacing: '.14em', color: silver, opacity: reveal}}>LABOR-FORCE BOUNDARY</div>
      {items.map((item, index) => {
        const x = 960 + item.x * move;
        const y = 500 + item.y * move;
        const toward = index < 2 ? -1 : 1;
        return (
          <div
            key={item.label}
            style={{
              position: 'absolute',
              left: x + toward * (1 - move) * 40,
              top: y,
              width: 300,
              opacity: progress(frame, start + 50 + index * 14, start + 82 + index * 14),
              transform: `translate(-50%,-50%)`,
              color: item.color,
            }}
          >
            <div style={{fontFamily: sans, fontSize: 62, fontWeight: 780, letterSpacing: '-.04em'}}>{item.value}</div>
            <div style={{fontFamily: sans, fontSize: 16, letterSpacing: '.14em', color: silver, marginTop: 5}}>{item.label}</div>
          </div>
        );
      })}
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 78, textAlign: 'center', opacity: rate}}>
        <span style={{fontFamily: sans, fontSize: 138, fontWeight: 800, letterSpacing: '-.07em', color: paper}}>4.1%</span>
        <span style={{fontFamily: serif, fontSize: 38, color: paper, marginLeft: 30}}>fell without more household employment</span>
      </div>
      <SourceTag>BLS HOUSEHOLD SURVEY · JULY 2026 · MONTH-TO-MONTH CHANGE</SourceTag>
    </AbsoluteFill>
  );
};

const ParticipationTrace: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const draw = progress(frame, start + 26, start + 110, Easing.out(Easing.cubic));
  const caveat = progress(frame, start + 210, start + 250);
  const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL'];
  const participation = [62.1, 61.9, 61.8, 61.8, 61.7, 61.5, 61.4];
  const emratio = [59.4, 59.2, 59.2, 59.2, 59.1, 59.0, 58.9];
  const path = (values: number[], base: number, amplitude: number) =>
    values.map((v, i) => `${i === 0 ? 'M' : 'L'} ${240 + i * 240} ${base + (values[0] - v) * amplitude}`).join(' ');
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 18), background: '#0C151A'}}>
      <div style={{position: 'absolute', left: 102, top: 82, fontFamily: serif, fontSize: 70}}>The denominator weakened too.</div>
      <svg width="1920" height="1080" style={{position: 'absolute', inset: 0}}>
        <path d={path(participation, 400, 310)} fill="none" stroke={copper} strokeWidth="7" strokeLinecap="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - draw} />
        <path d={path(emratio, 680, 390)} fill="none" stroke={cyan} strokeWidth="5" strokeLinecap="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - draw} />
        {months.map((m, i) => <text key={m} x={230 + i * 240} y="892" fill="rgba(241,238,231,.55)" fontFamily={sans} fontSize="17" letterSpacing="2">{m}</text>)}
      </svg>
      <div style={{position: 'absolute', right: 116, top: 305, textAlign: 'right', opacity: draw}}>
        <div style={{fontFamily: sans, fontSize: 78, fontWeight: 760, color: copper}}>−0.7 pp</div>
        <div style={{fontFamily: sans, fontSize: 18, letterSpacing: '.13em', color: silver}}>LABOR-FORCE PARTICIPATION · SINCE JANUARY</div>
      </div>
      <div style={{position: 'absolute', right: 116, top: 612, textAlign: 'right', opacity: draw}}>
        <div style={{fontFamily: sans, fontSize: 72, fontWeight: 760, color: cyan}}>−0.5 pp</div>
        <div style={{fontFamily: sans, fontSize: 18, letterSpacing: '.13em', color: silver}}>EMPLOYMENT–POPULATION RATIO · SINCE JANUARY</div>
      </div>
      <div style={{position: 'absolute', left: 102, bottom: 58, fontFamily: sans, fontSize: 17, color: silver, opacity: caveat, letterSpacing: '.08em'}}>
        JANUARY 2026 POPULATION-CONTROL BREAK IS NOT SHOWN AS ECONOMIC MOVEMENT
      </div>
      <SourceTag>BLS HOUSEHOLD SURVEY · SEASONALLY ADJUSTED</SourceTag>
    </AbsoluteFill>
  );
};

const SurveyDivergence: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const diverge = progress(frame, start + 30, start + 132, Easing.inOut(Easing.cubic));
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 18), background: paper, color: ink}}>
      <div style={{position: 'absolute', left: 104, top: 88, fontFamily: serif, fontSize: 66}}>Same labor market. Different measuring instruments.</div>
      <div style={{position: 'absolute', left: 104, top: 184, fontFamily: sans, fontSize: 18, letterSpacing: '.14em', color: '#657277'}}>FEBRUARY → JULY 2026 · BEGINNING AFTER THE CONTROL BREAK</div>
      <svg width="1920" height="1080" style={{position: 'absolute', inset: 0}}>
        <line x1="250" y1="530" x2="1670" y2="530" stroke="rgba(8,16,21,.18)" />
        <path d={`M 250 530 C 680 500 1180 ${500 - 140 * diverge} 1650 ${530 - 225 * diverge}`} fill="none" stroke={copper} strokeWidth="10" strokeLinecap="round" />
        <path d={`M 250 530 C 680 560 1180 ${565 + 160 * diverge} 1650 ${530 + 285 * diverge}`} fill="none" stroke={cyan} strokeWidth="8" strokeLinecap="round" />
      </svg>
      <div style={{position: 'absolute', right: 112, top: 258, textAlign: 'right', opacity: diverge}}>
        <div style={{fontFamily: sans, fontSize: 86, fontWeight: 800, color: copper}}>+422K</div>
        <div style={{fontFamily: sans, fontSize: 18, letterSpacing: '.12em'}}>PAYROLL EMPLOYMENT</div>
      </div>
      <div style={{position: 'absolute', right: 112, top: 716, textAlign: 'right', opacity: diverge}}>
        <div style={{fontFamily: sans, fontSize: 86, fontWeight: 800, color: '#379F9B'}}>−563K</div>
        <div style={{fontFamily: sans, fontSize: 18, letterSpacing: '.12em'}}>CONCEPT-ADJUSTED HOUSEHOLD SERIES</div>
      </div>
      <div style={{position: 'absolute', left: 104, bottom: 82, width: 760, fontFamily: serif, fontSize: 31, lineHeight: 1.4, color: '#344146'}}>
        Neither series is “the lie.” The household survey is smaller, noisier, and counts a different concept.
      </div>
      <SourceTag color="#536267">BLS · EMPLOYMENT SITUATION · SURVEY CONCEPT COMPARISON</SourceTag>
    </AbsoluteFill>
  );
};

const EmptyConclusion: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const fade = progress(frame, start + 20, start + 62);
  const disappear = progress(frame, start + 150, end - 24);
  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 16)}}>
      <FullBleedVideo src="assets/documentary/empty_office_pexels_7844843.mp4" startFrom={85} muted style={{filter: 'saturate(.45) brightness(.52)', transform: `scale(${1.1 + disappear * 0.035})`}} />
      <AbsoluteFill style={{background: `rgba(4,10,13,${0.44 + disappear * 0.28})`}} />
      <div style={{position: 'absolute', left: 112, bottom: 158, width: 1050, opacity: fade * (1 - disappear * 0.35)}}>
        <div style={{fontFamily: serif, fontSize: 80, lineHeight: 1.02, letterSpacing: '-.04em'}}>The rate fell.</div>
        <div style={{fontFamily: serif, fontSize: 80, lineHeight: 1.02, letterSpacing: '-.04em', color: copper}}>Employment did not rise.</div>
        <div style={{fontFamily: sans, fontSize: 21, letterSpacing: '.13em', color: silver, marginTop: 36}}>THE NUMBER LEAVES. THE EMPTY CHAIR REMAINS.</div>
      </div>
    </AbsoluteFill>
  );
};

export const Chapter02: React.FC<ChapterProps> = ({durationInFrames}) => {
  const a = Math.round(durationInFrames * 0.18);
  const b = Math.round(durationInFrames * 0.46);
  const c = Math.round(durationInFrames * 0.68);
  const d = Math.round(durationInFrames * 0.88);
  return (
    <Canvas>
      <SurveyGrammar start={0} end={a + 16} />
      <ParadoxRoom start={a - 12} end={b + 18} />
      <ParticipationTrace start={b - 12} end={c + 18} />
      <SurveyDivergence start={c - 12} end={d + 16} />
      <EmptyConclusion start={d - 10} end={durationInFrames} />
      <Audio src={staticFile('assets/audio/narration/chapter_02.wav')} volume={1} />
      <Audio src={staticFile('assets/audio/sound/chapter_02_bed.m4a')} volume={0.76} />
      <Vignette strength={0.48} />
      <FilmGrain opacity={0.08} />
    </Canvas>
  );
};
