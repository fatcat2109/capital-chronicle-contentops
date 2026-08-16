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

const releasePaper: React.CSSProperties = {
  position: 'absolute',
  background: '#EEEAE0',
  color: '#172126',
  boxShadow: '0 28px 70px rgba(0,0,0,.34)',
  border: '1px solid rgba(16,29,35,.18)',
  overflow: 'hidden',
};

const CompensationDocuments: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const span = end - start;
  const earnings = progress(frame, start + span * 0.05, start + span * 0.22, Easing.out(Easing.cubic));
  const eci = progress(frame, start + span * 0.3, start + span * 0.49, Easing.out(Easing.cubic));
  const resolve = progress(frame, start + span * 0.61, start + span * 0.83, Easing.inOut(Easing.cubic));

  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 14), background: '#071116'}}>
      <ChapterSlug number={6} opacity={earnings}>The missing share</ChapterSlug>
      <div style={{position: 'absolute', left: 102, top: 154, width: 920, fontFamily: serif, fontSize: 68, lineHeight: 1.04}}>
        Start with what the official releases actually measured.
      </div>

      <div
        style={{
          ...releasePaper,
          left: 116,
          top: 375,
          width: 890,
          height: 500,
          opacity: earnings,
          transform: `translate(${resolve * 88}px, ${(1 - earnings) * 34}px) rotate(${-1.1 + resolve * 1.1}deg)`,
        }}
      >
        <div style={{height: 58, padding: '20px 34px', borderBottom: '1px solid rgba(16,29,35,.18)', fontFamily: sans, fontSize: 15, fontWeight: 760, letterSpacing: '.16em'}}>
          U.S. BUREAU OF LABOR STATISTICS · EMPLOYMENT SITUATION
        </div>
        <div style={{padding: '46px 48px'}}>
          <div style={{fontFamily: sans, fontSize: 16, letterSpacing: '.14em', color: '#526066'}}>AVERAGE HOURLY EARNINGS · JULY 2026</div>
          <div style={{display: 'flex', alignItems: 'baseline', gap: 24, marginTop: 24}}>
            <span style={{fontFamily: sans, fontSize: 126, fontWeight: 840, letterSpacing: '-.07em', color: '#177E88'}}>+3.2%</span>
            <span style={{fontFamily: serif, fontSize: 31}}>over the year</span>
          </div>
          <div style={{height: 9, width: `${34 + resolve * 48}%`, marginTop: 34, background: cyan, opacity: 0.72}} />
          <div style={{fontFamily: serif, fontSize: 25, marginTop: 28, color: '#3D4A4F'}}>A direct pay reading, exposed to changes in the mix of jobs.</div>
        </div>
      </div>

      <div
        style={{
          ...releasePaper,
          right: 116,
          top: 346,
          width: 810,
          height: 500,
          opacity: eci,
          transform: `translate(${-resolve * 88}px, ${(1 - eci) * 34}px) rotate(${1.2 - resolve * 1.2}deg)`,
        }}
      >
        <div style={{height: 58, padding: '20px 34px', borderBottom: '1px solid rgba(16,29,35,.18)', fontFamily: sans, fontSize: 15, fontWeight: 760, letterSpacing: '.16em'}}>
          U.S. BUREAU OF LABOR STATISTICS · EMPLOYMENT COST INDEX
        </div>
        <div style={{padding: '46px 48px'}}>
          <div style={{fontFamily: sans, fontSize: 16, letterSpacing: '.14em', color: '#526066'}}>PRIVATE-INDUSTRY WAGES · Q2 2026</div>
          <div style={{display: 'flex', alignItems: 'baseline', gap: 24, marginTop: 24}}>
            <span style={{fontFamily: sans, fontSize: 126, fontWeight: 840, letterSpacing: '-.07em', color: copper}}>+3.1%</span>
            <span style={{fontFamily: serif, fontSize: 31}}>over the year</span>
          </div>
          <div style={{height: 9, width: `${33 + resolve * 49}%`, marginTop: 34, background: copper, opacity: 0.78}} />
          <div style={{fontFamily: serif, fontSize: 25, marginTop: 28, color: '#3D4A4F'}}>Controls more carefully for shifts in job and industry mix.</div>
        </div>
      </div>

      <div style={{position: 'absolute', left: 0, right: 0, bottom: 91, textAlign: 'center', opacity: resolve, fontFamily: sans, fontSize: 18, fontWeight: 760, letterSpacing: '.17em', color: silver}}>
        TWO METHODS · ONE ROUGHLY 3% WAGE READING
      </div>
      <SourceTag>BLS · EMPLOYMENT SITUATION / EMPLOYMENT COST INDEX · OFFICIAL RELEASES</SourceTag>
    </AbsoluteFill>
  );
};

const PriceRelease: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const span = end - start;
  const page = progress(frame, start + span * 0.04, start + span * 0.19, Easing.out(Easing.cubic));
  const crossing = progress(frame, start + span * 0.22, start + span * 0.51, Easing.inOut(Easing.cubic));
  const real = progress(frame, start + span * 0.48, start + span * 0.65, Easing.out(Easing.cubic));
  const complication = progress(frame, start + span * 0.67, start + span * 0.83, Easing.out(Easing.cubic));

  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 14), background: paper, color: ink}}>
      <div style={{position: 'absolute', left: 103, top: 77, fontFamily: serif, fontSize: 64}}>Then the price release changes the meaning of the same number.</div>
      <div style={{position: 'absolute', left: 104, top: 182, fontFamily: sans, fontSize: 15, fontWeight: 760, letterSpacing: '.17em', color: '#68777C'}}>
        BLS CONSUMER PRICE INDEX · JULY 2026 · OFFICIAL RELEASE
      </div>

      <div style={{position: 'absolute', left: 118, top: 290, width: 1180, height: 420, opacity: page}}>
        <div style={{position: 'absolute', left: 0, top: 0, width: 1130, height: 2, background: 'rgba(16,29,35,.19)'}} />
        <div style={{position: 'absolute', left: 0, top: 96, width: `${43 + crossing * 29}%`, height: 100, background: 'rgba(69,184,194,.73)'}} />
        <div style={{position: 'absolute', left: 0, top: 245, width: `${45 + crossing * 31}%`, height: 100, background: 'rgba(201,74,72,.82)'}} />
        <div style={{position: 'absolute', left: 26, top: 116, fontFamily: sans, fontSize: 47, fontWeight: 840}}>+3.2%</div>
        <div style={{position: 'absolute', left: 26, top: 265, fontFamily: sans, fontSize: 47, fontWeight: 840, color: paper}}>+3.4%</div>
        <div style={{position: 'absolute', right: 0, top: 122, fontFamily: sans, fontSize: 16, fontWeight: 760, letterSpacing: '.13em'}}>HOURLY EARNINGS · YEAR OVER YEAR</div>
        <div style={{position: 'absolute', right: 0, top: 271, fontFamily: sans, fontSize: 16, fontWeight: 760, letterSpacing: '.13em'}}>HEADLINE CPI · YEAR OVER YEAR</div>
      </div>

      <div style={{position: 'absolute', right: 102, top: 345, width: 420, opacity: real, borderLeft: `3px solid ${red}`, paddingLeft: 34}}>
        <div style={{fontFamily: sans, fontSize: 106, fontWeight: 850, letterSpacing: '-.07em', color: red}}>−0.2%</div>
        <div style={{fontFamily: serif, fontSize: 30, lineHeight: 1.12}}>real average hourly earnings</div>
      </div>

      <div style={{position: 'absolute', left: 105, right: 105, bottom: 92, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', opacity: complication}}>
        <div style={{display: 'flex', alignItems: 'baseline', gap: 18}}>
          <span style={{fontFamily: sans, fontSize: 52, fontWeight: 830, color: cyan}}>2.5%</span>
          <span style={{fontFamily: sans, fontSize: 15, fontWeight: 760, letterSpacing: '.13em'}}>CORE CPI · EX FOOD &amp; ENERGY</span>
          <span style={{fontFamily: serif, fontSize: 24, color: '#58666B'}}>energy helped lift the headline</span>
        </div>
        <div style={{textAlign: 'right'}}>
          <div style={{fontFamily: sans, fontSize: 39, fontWeight: 830, color: copper}}>+6.0%</div>
          <div style={{fontFamily: sans, fontSize: 13, lineHeight: 1.35, fontWeight: 760, letterSpacing: '.11em'}}>PRIVATE-INDUSTRY HEALTH-INSURANCE<br />BENEFIT COSTS · Q2 2026 ECI</div>
        </div>
      </div>
      <SourceTag color="#536267">BLS · JULY 2026 CPI / REAL EARNINGS · Q2 2026 ECI</SourceTag>
    </AbsoluteFill>
  );
};

const TransactionDetail: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const local = progress(frame, start, end);
  const reveal = progress(frame, start + 8, start + 35, Easing.out(Easing.cubic));

  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 10), background: '#060D11'}}>
      <FullBleedVideo
        src="assets/documentary/grocery_cashier_pexels_4121754.mp4"
        startFrom={70}
        muted
        style={{filter: 'saturate(.38) brightness(.54) contrast(1.08)', transform: `scale(${1.03 + local * 0.025})`, objectPosition: 'center 46%'}}
      />
      <AbsoluteFill style={{background: 'linear-gradient(90deg,rgba(3,9,12,.92) 0%,rgba(3,9,12,.57) 46%,rgba(3,9,12,.3) 72%,rgba(3,9,12,.76) 100%)'}} />
      <div style={{position: 'absolute', left: 101, top: 162, width: 665, opacity: reveal}}>
        <div style={{fontFamily: serif, fontSize: 68, lineHeight: 1.02}}>Where nominal pay meets current prices.</div>
        <div style={{marginTop: 38, height: 2, width: 110, background: copper}} />
        <div style={{marginTop: 29, display: 'flex', alignItems: 'baseline', gap: 21}}>
          <span style={{fontFamily: sans, fontSize: 70, fontWeight: 840, color: red}}>−0.2%</span>
          <span style={{fontFamily: sans, fontSize: 15, lineHeight: 1.4, fontWeight: 760, letterSpacing: '.13em', color: silver}}>REAL AVERAGE<br />HOURLY EARNINGS</span>
        </div>
      </div>
      <SourceTag>SHORT ILLUSTRATIVE TRANSACTION · NO CLAIM ABOUT THE PICTURED PEOPLE</SourceTag>
    </AbsoluteFill>
  );
};

const QuitsThreshold: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const span = end - start;
  const enter = progress(frame, start + span * 0.05, start + span * 0.28, Easing.out(Easing.cubic));
  const narrow = progress(frame, start + span * 0.43, start + span * 0.77, Easing.inOut(Easing.cubic));

  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 11), background: '#071015'}}>
      <FullBleedVideo
        src="assets/documentary/job_interview_pexels_5438891.mp4"
        startFrom={80}
        muted
        style={{filter: 'saturate(.32) brightness(.45) contrast(1.12)', transform: 'scale(1.05)', objectPosition: '58% center'}}
      />
      <AbsoluteFill style={{background: `linear-gradient(90deg,rgba(3,8,11,.96) 0%,rgba(3,8,11,.89) ${42 + narrow * 8}%,rgba(3,8,11,.28) ${72 - narrow * 4}%,rgba(3,8,11,.76) 100%)`}} />
      <div style={{position: 'absolute', left: 745 + narrow * 45, top: 104, width: 500 - narrow * 90, height: 820, border: '2px solid rgba(241,238,231,.28)', borderBottom: 0, boxShadow: '0 0 0 999px rgba(4,10,13,.08)'}} />
      <div style={{position: 'absolute', left: 101, top: 158, width: 610, opacity: enter}}>
        <div style={{fontFamily: sans, fontSize: 16, fontWeight: 760, letterSpacing: '.17em', color: copper}}>THE DOORWAY RETURNS</div>
        <div style={{fontFamily: serif, fontSize: 68, lineHeight: 1.02, marginTop: 27}}>Fewer completed moves.<br />Less leverage to leave.</div>
        <div style={{fontFamily: sans, fontSize: 16, lineHeight: 1.55, letterSpacing: '.08em', color: silver, marginTop: 36, width: 570}}>
          LOW QUITS MAY CONSTRAIN BARGAINING POWER.<br />ANALYTICAL LIMIT — NOT A MEASURED CAUSAL COEFFICIENT.
        </div>
      </div>
      <SourceTag>ILLUSTRATIVE INTERVIEW THRESHOLD · NO CLAIM ABOUT THE PICTURED PEOPLE</SourceTag>
    </AbsoluteFill>
  );
};

const ProductivityDocument: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const span = end - start;
  const arrive = progress(frame, start + span * 0.04, start + span * 0.24, Easing.out(Easing.cubic));
  const underline = progress(frame, start + span * 0.28, start + span * 0.56, Easing.inOut(Easing.cubic));
  const yieldTrace = progress(frame, start + span * 0.63, start + span * 0.9, Easing.inOut(Easing.cubic));

  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 14), background: '#081115'}}>
      <div
        style={{
          ...releasePaper,
          left: 132 - yieldTrace * 54,
          top: 88 + (1 - arrive) * 38,
          width: 1160,
          height: 840,
          opacity: arrive,
        }}
      >
        <div style={{height: 78, padding: '27px 42px', background: '#DCD8CD', borderBottom: '1px solid rgba(16,29,35,.22)', display: 'flex', justifyContent: 'space-between', fontFamily: sans, fontSize: 15, fontWeight: 780, letterSpacing: '.15em'}}>
          <span>U.S. BUREAU OF LABOR STATISTICS</span>
          <span>PRODUCTIVITY AND COSTS · Q2 2026</span>
        </div>
        <div style={{padding: '58px 66px'}}>
          <div style={{fontFamily: serif, fontSize: 50, lineHeight: 1.06}}>Nonfarm business sector</div>
          <div style={{fontFamily: sans, fontSize: 14, fontWeight: 760, letterSpacing: '.16em', color: '#5C696E', marginTop: 18}}>PRELIMINARY ESTIMATE</div>
          <div style={{marginTop: 78, fontFamily: sans, fontSize: 17, fontWeight: 760, letterSpacing: '.13em', color: '#536267'}}>LABOR SHARE · Q2 2026</div>
          <div style={{display: 'flex', alignItems: 'baseline', gap: 30, marginTop: 12}}>
            <span style={{fontFamily: sans, fontSize: 160, fontWeight: 860, letterSpacing: '-.08em', color: red}}>52.9%</span>
            <span style={{border: `2px solid ${copper}`, padding: '10px 18px', fontFamily: sans, fontSize: 16, fontWeight: 800, letterSpacing: '.17em', color: '#9B4E30'}}>PRELIMINARY</span>
          </div>
          <div style={{height: 9, width: `${underline * 82}%`, background: copper, marginTop: 12}} />
          <div style={{fontFamily: sans, fontSize: 14, fontWeight: 790, letterSpacing: '.14em', color: '#536267', marginTop: 19}}>LOWEST READING IN THE 1947–2026 SERIES</div>
          <div style={{marginTop: 52, paddingTop: 28, borderTop: '1px solid rgba(16,29,35,.17)', fontFamily: sans, fontSize: 16, lineHeight: 1.65, fontWeight: 690, letterSpacing: '.08em', color: '#46555A'}}>
            REVISION-PRONE · CANNOT IDENTIFY WHY THE SHARE MOVED<br />AN UNSETTLED CLUE · NOT SUFFICIENT TO CARRY THE THESIS BY ITSELF
          </div>
        </div>
      </div>

      <div style={{position: 'absolute', left: 1230, right: 0, top: 536, height: 8, background: cyan, transformOrigin: 'left center', transform: `scaleX(${yieldTrace})`, opacity: yieldTrace * 0.72}} />
      <div style={{position: 'absolute', right: 102, top: 145, width: 410, opacity: yieldTrace, fontFamily: serif, fontSize: 43, lineHeight: 1.13, color: silver}}>
        The document opens into the full historical span.
      </div>
      <SourceTag>BLS PRODUCTIVITY AND COSTS · Q2 2026 · NATIVE RECONSTRUCTION OF OFFICIAL RELEASE</SourceTag>
    </AbsoluteFill>
  );
};

const LaborShareField: React.FC<{start: number; end: number}> = ({start, end}) => {
  const frame = useCurrentFrame();
  const span = end - start;
  const draw = progress(frame, start + span * 0.02, start + span * 0.34, Easing.out(Easing.cubic));
  const endpoint = progress(frame, start + span * 0.27, start + span * 0.4, Easing.out(Easing.cubic));
  const limits = progress(frame, start + span * 0.24, start + span * 0.33, Easing.out(Easing.cubic));
  const synthesis = progress(frame, start + span * 0.69, start + span * 0.8, Easing.out(Easing.cubic));
  const handoff = progress(frame, start + span * 0.9, start + span * 0.97, Easing.out(Easing.cubic));
  const d = 'M 140 512 C 260 420 340 575 470 472 S 680 590 820 485 S 1030 555 1160 500 S 1380 628 1510 565 S 1660 640 1770 690';

  return (
    <AbsoluteFill style={{opacity: holdFade(frame, start, end, 16), background: '#071115'}}>
      <div style={{position: 'absolute', left: 102, top: 76, width: 930, opacity: 1 - handoff, fontFamily: serif, fontSize: 64, lineHeight: 1.04}}>
        A long record.<br />An unsettled distributional clue.
      </div>
      <div style={{position: 'absolute', right: 102, top: 97, fontFamily: sans, fontSize: 16, fontWeight: 760, letterSpacing: '.16em', color: copper}}>
        NONFARM BUSINESS SECTOR · 1947–2026
      </div>

      <svg width="1920" height="1080" style={{position: 'absolute', inset: 0}}>
        <line x1="140" y1="690" x2="1770" y2="690" stroke="rgba(241,238,231,.11)" />
        <path d={d} fill="none" stroke="rgba(69,184,194,.22)" strokeWidth="18" strokeLinecap="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - draw} />
        <path d={d} fill="none" stroke={cyan} strokeWidth="6" strokeLinecap="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - draw} />
        <circle cx="1770" cy="690" r={10 + endpoint * 10} fill={red} opacity={endpoint} />
        <line x1="1770" y1="690" x2="1770" y2="438" stroke="rgba(201,74,72,.38)" strokeWidth="2" strokeDasharray="7 11" opacity={endpoint} />
      </svg>

      <div style={{position: 'absolute', left: 140, top: 726, fontFamily: sans, fontSize: 16, fontWeight: 760, letterSpacing: '.14em', color: silver}}>1947</div>
      <div style={{position: 'absolute', right: 102, top: 420, width: 420, textAlign: 'right', opacity: endpoint}}>
        <div style={{fontFamily: sans, fontSize: 128, fontWeight: 860, letterSpacing: '-.08em', color: red}}>52.9%</div>
        <div style={{fontFamily: sans, fontSize: 17, fontWeight: 760, letterSpacing: '.14em'}}>LABOR SHARE · Q2 2026</div>
        <div style={{fontFamily: sans, fontSize: 13, fontWeight: 760, letterSpacing: '.13em', color: silver, marginTop: 9}}>LOWEST READING · 1947–2026 SERIES</div>
        <div style={{display: 'inline-block', marginTop: 17, border: `2px solid ${copper}`, padding: '9px 15px', fontFamily: sans, fontSize: 14, fontWeight: 820, letterSpacing: '.18em', color: copper}}>PRELIMINARY</div>
      </div>

      <div style={{position: 'absolute', left: 102, top: 282, width: 760, minHeight: 210, opacity: synthesis * (1 - handoff)}}>
        <div style={{fontFamily: serif, fontSize: 52, lineHeight: 1.08}}>
          An economy can become more efficient<br /><span style={{color: copper}}>before it becomes more generous.</span>
        </div>
      </div>

      <div style={{position: 'absolute', left: 102, top: 283, width: 820, opacity: handoff}}>
        <div style={{fontFamily: sans, fontSize: 16, fontWeight: 780, letterSpacing: '.18em', color: copper}}>NO FORECAST · NO CAUSAL CLAIM</div>
        <div style={{fontFamily: serif, fontSize: 68, lineHeight: 1.04, marginTop: 25}}>The split now reaches<br />the policy institution.</div>
      </div>

      <div style={{position: 'absolute', left: 102, right: 102, bottom: 82, paddingTop: 19, borderTop: '1px solid rgba(241,238,231,.15)', display: 'flex', justifyContent: 'space-between', opacity: limits}}>
        <div style={{fontFamily: sans, fontSize: 14, fontWeight: 760, letterSpacing: '.13em', color: silver}}>
          PRELIMINARY · REVISION-PRONE · CANNOT IDENTIFY WHY THE SHARE MOVED
        </div>
        <div style={{fontFamily: sans, fontSize: 14, fontWeight: 760, letterSpacing: '.13em', color: silver}}>
          1947–2026 · NOT SUFFICIENT ON ITS OWN
        </div>
      </div>
      <SourceTag>BLS PRODUCTIVITY AND COSTS · Q2 2026 PRELIMINARY</SourceTag>
    </AbsoluteFill>
  );
};

export const Chapter06: React.FC<ChapterProps> = ({durationInFrames}) => {
  const payEnd = Math.round(durationInFrames * 0.2);
  const priceEnd = Math.round(durationInFrames * 0.35);
  const transactionEnd = Math.round(durationInFrames * 0.405);
  const thresholdEnd = Math.round(durationInFrames * 0.49);
  const documentEnd = Math.round(durationInFrames * 0.625);

  return (
    <Canvas>
      <CompensationDocuments start={0} end={payEnd + 16} />
      <PriceRelease start={payEnd - 12} end={priceEnd + 14} />
      <TransactionDetail start={priceEnd - 10} end={transactionEnd + 11} />
      <QuitsThreshold start={transactionEnd - 9} end={thresholdEnd + 13} />
      <ProductivityDocument start={thresholdEnd - 10} end={documentEnd + 15} />
      <LaborShareField start={documentEnd - 14} end={durationInFrames} />
      <Audio src={staticFile('assets/audio/narration/chapter_06.wav')} volume={1} />
      <Audio src={staticFile('assets/audio/sound/chapter_06_bed.m4a')} volume={0.74} />
      <Vignette strength={0.42} />
      <FilmGrain opacity={0.08} />
    </Canvas>
  );
};
