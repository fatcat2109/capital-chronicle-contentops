import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {localeLayout, stringsFor, type Locale, type StringKey} from './strings';
import {beats, captionCuesFor} from './timing';

const ink = '#071116';
const paper = '#F2EFE7';
const fog = '#AEBBC0';
const cyan = '#74D0C7';
const copper = '#E27E51';
const ice = '#9EC7D1';
const yellow = '#E5B566';
const sans = 'Manrope, Arial, sans-serif';
const serif = 'Source Serif 4, Georgia, serif';

export type ShortProps = {
  locale: Locale;
  burnedCaptions: boolean;
  narrationSrc: string;
  narrationEnabled: boolean;
};

const p = (
  frame: number,
  start: number,
  end: number,
  easing = Easing.inOut(Easing.cubic),
) =>
  interpolate(frame, [start, end], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing,
  });

const beatOpacity = (frame: number, duration: number, fade = 15) =>
  Math.min(p(frame, 0, fade, Easing.out(Easing.quad)), 1 - p(frame, duration - fade, duration));

const AssetVideo: React.FC<{
  src: string;
  startFrom?: number;
  opacity?: number;
  scale?: number;
  x?: number;
  y?: number;
  filter?: string;
  objectPosition?: string;
}> = ({
  src,
  startFrom = 0,
  opacity = 1,
  scale = 1,
  x = 0,
  y = 0,
  filter = 'saturate(.72) contrast(1.08)',
  objectPosition = '50% 50%',
}) => (
  <OffthreadVideo
    src={staticFile(src)}
    startFrom={startFrom}
    muted
    style={{
      position: 'absolute',
      inset: 0,
      width: '100%',
      height: '100%',
      objectFit: 'cover',
      objectPosition,
      opacity,
      filter,
      transform: `translate(${x}px, ${y}px) scale(${scale})`,
    }}
  />
);

const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        pointerEvents: 'none',
        opacity: 0.085,
        mixBlendMode: 'soft-light',
        transform: `translate(${(frame * 17) % 5 - 2}px, ${(frame * 29) % 5 - 2}px)`,
        backgroundImage:
          'url("data:image/svg+xml,%3Csvg viewBox=%270 0 160 160%27 xmlns=%27http://www.w3.org/2000/svg%27%3E%3Cfilter id=%27n%27%3E%3CfeTurbulence type=%27fractalNoise%27 baseFrequency=%27.88%27 numOctaves=%273%27 stitchTiles=%27stitch%27/%3E%3C/filter%3E%3Crect width=%27100%25%27 height=%27100%25%27 filter=%27url(%23n)%27 opacity=%27.6%27/%3E%3C/svg%3E")',
      }}
    />
  );
};

const BrandRail: React.FC<{t: (key: StringKey) => string; dark?: boolean}> = ({t, dark = false}) => (
  <div
    style={{
      position: 'absolute',
      left: 54,
      right: 54,
      top: 48,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      zIndex: 30,
      fontFamily: sans,
      fontSize: 16,
      fontWeight: 700,
      letterSpacing: '.17em',
      color: dark ? ink : paper,
    }}
  >
    <span>{t('brand.eyebrow')}</span>
    <span style={{display: 'flex', gap: 7}}>
      {[0, 1, 2].map((dot) => (
        <span key={dot} style={{width: 6, height: 6, borderRadius: 9, background: dot === 1 ? copper : cyan}} />
      ))}
    </span>
  </div>
);

const SourceLine: React.FC<{children: React.ReactNode; dark?: boolean}> = ({children, dark = false}) => (
  <div
    style={{
      position: 'absolute',
      left: 54,
      right: 54,
      bottom: 44,
      zIndex: 35,
      fontFamily: sans,
      fontSize: 22,
      fontWeight: 650,
      letterSpacing: '.105em',
      lineHeight: 1.3,
      color: dark ? 'rgba(7,17,22,.7)' : 'rgba(242,239,231,.68)',
    }}
  >
    {children}
  </div>
);

const IllustrativeTag: React.FC<{t: (key: StringKey) => string}> = ({t}) => (
  <div
    style={{
      position: 'absolute',
      right: 48,
      top: 104,
      maxWidth: 570,
      padding: '10px 13px',
      zIndex: 25,
      background: 'rgba(7,17,22,.62)',
      borderLeft: `3px solid ${cyan}`,
      color: 'rgba(242,239,231,.76)',
      fontFamily: sans,
      fontSize: 22,
      fontWeight: 700,
      letterSpacing: '.085em',
      lineHeight: 1.25,
      textAlign: 'right',
    }}
  >
    {t('source.illustrative')}
  </div>
);

const Hook: React.FC<{t: (key: StringKey) => string; duration: number}> = ({t, duration}) => {
  const frame = useCurrentFrame();
  const enter = spring({frame, fps: 30, config: {damping: 18, stiffness: 90, mass: 0.9}});
  const split = p(frame, 38, 90, Easing.out(Easing.cubic));
  const question = p(frame, 82, 118, Easing.out(Easing.quad));
  const drift = p(frame, 0, duration);
  return (
    <AbsoluteFill style={{opacity: beatOpacity(frame, duration), background: ink, color: paper}}>
      <AssetVideo
        src="assets/documentary/commuters_subway_cc0_pexels_855749.mp4"
        startFrom={32}
        scale={1.08 + drift * 0.055}
        x={-24 + drift * 28}
        filter="saturate(.42) brightness(.48) contrast(1.18)"
      />
      <AbsoluteFill style={{background: 'linear-gradient(180deg,rgba(4,10,13,.52),rgba(4,10,13,.2) 35%,rgba(4,10,13,.88) 90%)'}} />
      {[0, 1, 2, 3].map((panel) => (
        <div
          key={panel}
          style={{
            position: 'absolute',
            left: panel * 270,
            top: -50,
            bottom: -50,
            width: 270,
            borderRight: '1px solid rgba(158,199,209,.24)',
            background: panel % 2 === 0 ? 'rgba(133,188,201,.035)' : 'rgba(4,10,13,.08)',
            transform: `translateY(${(1 - enter) * (panel % 2 === 0 ? -110 : 110)}px)`,
          }}
        />
      ))}
      <BrandRail t={t} />
      <IllustrativeTag t={t} />
      <div style={{position: 'absolute', left: 58, right: 58, top: 520}}>
        <div
          style={{
            fontFamily: sans,
            fontWeight: 820,
            fontSize: 92,
            letterSpacing: '-.065em',
            lineHeight: 0.92,
            transform: `translateX(${(1 - split) * -70}px)`,
            opacity: enter,
          }}
        >
          {t('hook.jobs')}
        </div>
        <div style={{height: 3, margin: '29px 0 27px', background: `linear-gradient(90deg,${copper},transparent)`, transform: `scaleX(${split})`, transformOrigin: 'left'}} />
        <div
          style={{
            marginLeft: 96,
            fontFamily: serif,
            fontWeight: 600,
            fontSize: 88,
            letterSpacing: '-.05em',
            lineHeight: 0.94,
            color: ice,
            transform: `translateX(${(1 - split) * 70}px)`,
            opacity: enter,
          }}
        >
          {t('hook.unemployment')}
        </div>
      </div>
      <div
        style={{
          position: 'absolute',
          left: 60,
          bottom: 320,
          fontFamily: sans,
          fontSize: 28,
          fontWeight: 700,
          letterSpacing: '.09em',
          color: paper,
          opacity: question,
          transform: `translateY(${(1 - question) * 18}px)`,
        }}
      >
        {t('hook.question')}
      </div>
      <SourceLine>{t('source.bls.employment')}</SourceLine>
    </AbsoluteFill>
  );
};

const Paradox: React.FC<{t: (key: StringKey) => string; duration: number}> = ({t, duration}) => {
  const frame = useCurrentFrame();
  const payroll = p(frame, 10, 72, Easing.out(Easing.cubic));
  const rate = p(frame, 70, 132, Easing.out(Easing.cubic));
  const clash = p(frame, 122, 176, Easing.out(Easing.quad));
  const drift = p(frame, 0, duration);
  return (
    <AbsoluteFill style={{opacity: beatOpacity(frame, duration), background: ink, color: paper}}>
      <AssetVideo
        src="assets/documentary/empty_office_pexels_7844843.mp4"
        startFrom={55}
        scale={1.12 + drift * 0.035}
        x={-95}
        filter="saturate(.32) brightness(.36) contrast(1.22)"
      />
      <AbsoluteFill style={{background: 'linear-gradient(110deg,rgba(4,10,13,.94),rgba(4,10,13,.46) 72%,rgba(4,10,13,.88))'}} />
      <BrandRail t={t} />
      <IllustrativeTag t={t} />
      <div
        style={{
          position: 'absolute',
          left: 55,
          top: 315,
          width: 660,
          padding: '42px 44px 38px',
          border: '1px solid rgba(242,239,231,.18)',
          borderLeft: `6px solid ${copper}`,
          background: 'rgba(7,17,22,.72)',
          opacity: payroll,
          transform: `translateX(${(1 - payroll) * -90}px) rotate(-1.5deg)`,
        }}
      >
        <div style={{fontFamily: sans, fontSize: 18, fontWeight: 700, letterSpacing: '.15em', color: fog}}>{t('paradox.payroll.label')}</div>
        <div style={{fontFamily: sans, fontSize: 152, fontWeight: 820, letterSpacing: '-.075em', lineHeight: .9, color: copper, marginTop: 21}}>{t('paradox.payroll.value')}</div>
        <div style={{fontFamily: sans, fontSize: 22, fontWeight: 700, letterSpacing: '.105em', color: paper, marginTop: 20}}>{t('paradox.payroll.period')}</div>
      </div>
      <div
        style={{
          position: 'absolute',
          right: 56,
          top: 845,
          width: 650,
          padding: '43px 44px 40px',
          border: '1px solid rgba(116,208,199,.36)',
          borderRight: `6px solid ${cyan}`,
          background: 'rgba(7,17,22,.76)',
          textAlign: 'right',
          opacity: rate,
          transform: `translateX(${(1 - rate) * 90}px) rotate(1.5deg)`,
        }}
      >
        <div style={{fontFamily: sans, fontSize: 18, fontWeight: 700, letterSpacing: '.15em', color: fog}}>{t('paradox.rate.label')}</div>
        <div style={{fontFamily: serif, fontSize: 165, fontWeight: 600, letterSpacing: '-.07em', lineHeight: .9, color: cyan, marginTop: 21}}>{t('paradox.rate.value')}</div>
        <div style={{fontFamily: sans, fontSize: 22, fontWeight: 700, letterSpacing: '.105em', color: paper, marginTop: 20}}>{t('paradox.rate.period')}</div>
      </div>
      <div style={{position: 'absolute', left: 492, top: 708, width: 96, height: 96, borderRadius: 96, border: `2px solid ${paper}`, display: 'grid', placeItems: 'center', opacity: clash, transform: `scale(${.72 + clash * .28})`, background: ink}}>
        <span style={{fontFamily: serif, fontSize: 44, color: yellow}}>&amp;</span>
      </div>
      <div style={{position: 'absolute', left: 58, right: 58, bottom: 185, paddingTop: 25, borderTop: '1px solid rgba(242,239,231,.2)', fontFamily: serif, fontSize: 27, lineHeight: 1.34, color: fog, opacity: clash}}>
        {t('paradox.caveat')}
      </div>
      <SourceLine>{t('source.bls.employment')}</SourceLine>
    </AbsoluteFill>
  );
};

const ChangeRow: React.FC<{
  label: string;
  value: string;
  color: string;
  magnitude: number;
  reveal: number;
}> = ({label, value, color, magnitude, reveal}) => (
  <div style={{position: 'relative', height: 180, opacity: reveal, transform: `translateY(${(1 - reveal) * 22}px)`}}>
    <div style={{display: 'flex', alignItems: 'baseline', justifyContent: 'space-between'}}>
      <span style={{fontFamily: sans, fontSize: 18, fontWeight: 700, letterSpacing: '.135em', color: fog}}>{label}</span>
      <span style={{fontFamily: sans, fontSize: 75, fontWeight: 820, letterSpacing: '-.055em', color}}>{value}</span>
    </div>
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 35, height: 8, background: 'rgba(242,239,231,.1)', overflow: 'hidden'}}>
      <div style={{width: `${magnitude * reveal}%`, height: '100%', background: color, boxShadow: `0 0 24px ${color}55`}} />
    </div>
  </div>
);

const Arithmetic: React.FC<{t: (key: StringKey) => string; duration: number}> = ({t, duration}) => {
  const frame = useCurrentFrame();
  const intro = p(frame, 10, 50, Easing.out(Easing.cubic));
  const row1 = p(frame, 48, 100, Easing.out(Easing.cubic));
  const row2 = p(frame, 95, 150, Easing.out(Easing.cubic));
  const row3 = p(frame, 142, 195, Easing.out(Easing.cubic));
  const rate = p(frame, 205, 272, Easing.out(Easing.back(1.35)));
  const answer = p(frame, 255, 312, Easing.out(Easing.cubic));
  return (
    <AbsoluteFill style={{opacity: beatOpacity(frame, duration), background: paper, color: ink}}>
      <BrandRail t={t} dark />
      <div style={{position: 'absolute', left: 56, right: 56, top: 162}}>
        <div style={{fontFamily: sans, fontSize: 17, fontWeight: 800, letterSpacing: '.18em', color: copper, opacity: intro}}>{t('arithmetic.kicker')}</div>
        <div style={{marginTop: 24, fontFamily: serif, fontSize: 61, lineHeight: 1.04, letterSpacing: '-.035em', opacity: intro}}>{t('arithmetic.subtitle.1')}<br />{t('arithmetic.subtitle.2')}</div>
      </div>
      <div style={{position: 'absolute', left: 58, right: 58, top: 480}}>
        <ChangeRow label={t('arithmetic.employment.label')} value={t('arithmetic.employment.value')} color={ink} magnitude={33} reveal={row1} />
        <ChangeRow label={t('arithmetic.laborForce.label')} value={t('arithmetic.laborForce.value')} color={copper} magnitude={100} reveal={row2} />
        <ChangeRow label={t('arithmetic.unemployed.label')} value={t('arithmetic.unemployed.value')} color="#369A97" magnitude={67} reveal={row3} />
      </div>
      <div
        style={{
          position: 'absolute',
          left: 54,
          right: 54,
          top: 1105,
          height: 420,
          borderTop: '1px solid rgba(7,17,22,.18)',
          borderBottom: '1px solid rgba(7,17,22,.18)',
          display: 'grid',
          placeItems: 'center',
          textAlign: 'center',
        }}
      >
        <div style={{opacity: rate, transform: `scale(${.82 + .18 * rate})`}}>
          <div style={{fontFamily: serif, fontSize: 170, lineHeight: .82, letterSpacing: '-.075em', color: '#287D7A'}}>{t('paradox.rate.value')}</div>
          <div style={{marginTop: 35, fontFamily: sans, fontSize: 20, fontWeight: 800, letterSpacing: '.15em'}}>{t('arithmetic.result.before')}</div>
          <div style={{marginTop: 10, fontFamily: sans, fontSize: 25, fontWeight: 800, letterSpacing: '.08em', color: copper}}>{t('arithmetic.result.after')}</div>
        </div>
      </div>
      <div style={{position: 'absolute', left: 58, right: 58, bottom: 102, fontFamily: serif, fontSize: 23, lineHeight: 1.35, color: '#56666C', opacity: answer}}>{t('arithmetic.caveat')}</div>
      <SourceLine dark>{t('source.bls.cps')}</SourceLine>
    </AbsoluteFill>
  );
};

const Door: React.FC<{
  label: string;
  thenValue: string;
  nowValue: string;
  color: string;
  index: number;
  frame: number;
  thenLabel: string;
  nowLabel: string;
}> = ({label, thenValue, nowValue, color, index, frame, thenLabel, nowLabel}) => {
  const reveal = p(frame, 38 + index * 25, 90 + index * 25, Easing.out(Easing.cubic));
  const close = p(frame, 128 + index * 22, 215 + index * 22, Easing.inOut(Easing.cubic));
  return (
    <div style={{position: 'relative', width: 296, height: 705, opacity: reveal}}>
      <div style={{height: 84, fontFamily: sans, fontSize: 18, lineHeight: 1.15, fontWeight: 800, letterSpacing: '.1em', color: paper}}>{label}</div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 92, bottom: 110, border: '1px solid rgba(242,239,231,.24)', overflow: 'hidden', background: 'rgba(7,17,22,.46)'}}>
        <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: `${close * 42}%`, background: `linear-gradient(180deg,${color}E8,${color}77)`, borderBottom: `2px solid ${color}`}} />
        <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: `${close * 42}%`, background: `linear-gradient(0deg,${color}E8,${color}77)`, borderTop: `2px solid ${color}`}} />
        <div style={{position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', opacity: 1 - close * .68}}>
          <div style={{textAlign: 'center'}}>
            <div style={{fontFamily: sans, fontSize: 22, fontWeight: 700, letterSpacing: '.1em', color: fog}}>{thenLabel}</div>
            <div style={{fontFamily: sans, fontSize: 58, fontWeight: 800, color: paper, marginTop: 5}}>{thenValue}</div>
          </div>
        </div>
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', paddingTop: 18, borderTop: `3px solid ${color}`}}>
        <span style={{fontFamily: sans, fontSize: 22, fontWeight: 750, letterSpacing: '.09em', color: fog}}>{nowLabel}</span>
        <span style={{fontFamily: sans, fontSize: 55, fontWeight: 820, letterSpacing: '-.045em', color}}>{nowValue}</span>
      </div>
    </div>
  );
};

const Doors: React.FC<{t: (key: StringKey) => string; duration: number}> = ({t, duration}) => {
  const frame = useCurrentFrame();
  const drift = p(frame, 0, duration);
  const title = p(frame, 6, 48, Easing.out(Easing.cubic));
  const thesis = p(frame, 295, 350, Easing.out(Easing.cubic));
  const dim = p(frame, 278, 330);
  return (
    <AbsoluteFill style={{opacity: beatOpacity(frame, duration), background: ink, color: paper}}>
      <AssetVideo
        src="assets/documentary/job_interview_pexels_5438891.mp4"
        startFrom={42}
        scale={1.22 + drift * .04}
        x={50}
        objectPosition="60% 50%"
        filter="saturate(.42) brightness(.38) contrast(1.18)"
      />
      <AbsoluteFill style={{background: `rgba(4,10,13,${.58 + dim * .34})`}} />
      <BrandRail t={t} />
      <IllustrativeTag t={t} />
      <div style={{position: 'absolute', left: 54, right: 54, top: 165, opacity: title}}>
        <div style={{fontFamily: sans, fontSize: 18, fontWeight: 800, letterSpacing: '.18em', color: yellow}}>{t('doors.kicker')}</div>
        <div style={{marginTop: 20, fontFamily: serif, fontSize: 56, lineHeight: 1.04}}>{t('doors.subtitle.1')}<br />{t('doors.subtitle.2')}</div>
      </div>
      <div style={{position: 'absolute', left: 54, right: 54, top: 440, display: 'flex', justifyContent: 'space-between', gap: 26, opacity: 1 - thesis * .82}}>
        <Door label={t('doors.hires')} thenValue={t('doors.hires.then')} nowValue={t('doors.hires.now')} thenLabel={t('doors.then')} nowLabel={t('doors.now')} color={cyan} index={0} frame={frame} />
        <Door label={t('doors.quits')} thenValue={t('doors.quits.then')} nowValue={t('doors.quits.now')} thenLabel={t('doors.then')} nowLabel={t('doors.now')} color={yellow} index={1} frame={frame} />
        <Door label={t('doors.layoffs')} thenValue={t('doors.layoffs.then')} nowValue={t('doors.layoffs.now')} thenLabel={t('doors.then')} nowLabel={t('doors.now')} color={copper} index={2} frame={frame} />
      </div>
      <div
        style={{
          position: 'absolute',
          left: 55,
          right: 55,
          top: 600,
          opacity: thesis,
          transform: `translateY(${(1 - thesis) * 35}px)`,
        }}
      >
        {[t('doors.thesis.1'), t('doors.thesis.2'), t('doors.thesis.3')].map((line, index) => (
          <div
            key={line}
            style={{
              padding: '28px 0 24px',
              borderBottom: '1px solid rgba(242,239,231,.22)',
              fontFamily: index === 1 ? serif : sans,
              fontSize: index === 1 ? 102 : 92,
              fontWeight: index === 1 ? 600 : 820,
              letterSpacing: '-.055em',
              color: index === 0 ? cyan : index === 1 ? yellow : copper,
            }}
          >
            {line}
          </div>
        ))}
        <div style={{marginTop: 40, maxWidth: 760, fontFamily: serif, fontSize: 28, lineHeight: 1.34, color: fog}}>{t('doors.caveat')}</div>
      </div>
      <SourceLine>{t('source.bls.jolts')}</SourceLine>
    </AbsoluteFill>
  );
};

const Engine: React.FC<{t: (key: StringKey) => string; duration: number}> = ({t, duration}) => {
  const frame = useCurrentFrame();
  const drift = p(frame, 0, duration);
  const demand = p(frame, 8, 58, Easing.out(Easing.cubic));
  const bars = p(frame, 82, 175, Easing.out(Easing.cubic));
  const product = p(frame, 168, 225, Easing.out(Easing.back(1.2)));
  const caveat = p(frame, 245, 292, Easing.out(Easing.quad));
  return (
    <AbsoluteFill style={{opacity: beatOpacity(frame, duration), background: ink, color: paper}}>
      <AssetVideo
        src="assets/documentary/warehouse_workers_pexels_4293958.mp4"
        startFrom={18}
        scale={1.18 + drift * .055}
        x={-30}
        filter="saturate(.52) brightness(.46) contrast(1.18)"
      />
      <AbsoluteFill style={{background: 'linear-gradient(180deg,rgba(4,10,13,.54),rgba(4,10,13,.84) 44%,rgba(4,10,13,.97) 68%)'}} />
      <BrandRail t={t} />
      <IllustrativeTag t={t} />
      <div style={{position: 'absolute', left: 55, right: 55, top: 165, opacity: demand}}>
        <div style={{fontFamily: sans, fontSize: 18, fontWeight: 800, letterSpacing: '.18em', color: yellow}}>{t('engine.kicker')}</div>
        <div style={{display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginTop: 27}}>
          <div style={{width: 620, whiteSpace: 'pre-line', fontFamily: sans, fontSize: 24, fontWeight: 700, lineHeight: 1.22, letterSpacing: '.055em'}}>{t('engine.demand.label')}</div>
          <div style={{fontFamily: serif, fontSize: 123, lineHeight: .8, letterSpacing: '-.07em', color: yellow}}>{t('engine.demand.value')}</div>
        </div>
        <div style={{marginTop: 22, fontFamily: sans, fontSize: 22, fontWeight: 700, letterSpacing: '.09em', color: fog}}>{t('engine.demand.note')}</div>
      </div>
      <div style={{position: 'absolute', left: 55, right: 55, top: 680, padding: '45px 40px 35px', background: 'rgba(7,17,22,.88)', border: '1px solid rgba(242,239,231,.14)'}}>
        <div style={{marginBottom: 30, fontFamily: sans, fontSize: 24, fontWeight: 800, letterSpacing: '.13em', color: fog}}>{t('engine.sector.label')}</div>
        <div style={{display: 'grid', gridTemplateColumns: '180px 1fr 150px', gap: 26, alignItems: 'center', marginBottom: 55}}>
          <div style={{fontFamily: sans, fontSize: 18, fontWeight: 800, letterSpacing: '.12em'}}>{t('engine.output.label')}</div>
          <div style={{height: 18, background: 'rgba(242,239,231,.09)', overflow: 'hidden'}}><div style={{height: '100%', width: `${bars * 100}%`, background: cyan, boxShadow: `0 0 28px ${cyan}66`}} /></div>
          <div style={{fontFamily: sans, fontSize: 56, fontWeight: 820, textAlign: 'right', color: cyan}}>{t('engine.output.value')}</div>
        </div>
        <div style={{display: 'grid', gridTemplateColumns: '180px 1fr 150px', gap: 26, alignItems: 'center'}}>
          <div style={{fontFamily: sans, fontSize: 18, fontWeight: 800, letterSpacing: '.12em'}}>{t('engine.hours.label')}</div>
          <div style={{height: 18, background: 'rgba(242,239,231,.09)', overflow: 'hidden'}}><div style={{height: '100%', width: `${bars * 8}%`, minWidth: bars * 10, background: copper, boxShadow: `0 0 22px ${copper}55`}} /></div>
          <div style={{fontFamily: sans, fontSize: 56, fontWeight: 820, textAlign: 'right', color: copper}}>{t('engine.hours.value')}</div>
        </div>
        <div style={{marginTop: 38, fontFamily: sans, fontSize: 22, fontWeight: 700, letterSpacing: '.09em', color: fog}}>{t('engine.period')}</div>
      </div>
      <div style={{position: 'absolute', left: 55, right: 55, top: 1160, height: 265, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 44px', borderTop: `2px solid ${ice}`, borderBottom: `2px solid ${ice}`, background: 'rgba(21,48,55,.72)', opacity: product, transform: `scale(${.95 + product * .05})`}}>
        <div>
          <div style={{fontFamily: sans, fontSize: 18, fontWeight: 800, letterSpacing: '.16em', color: ice}}>{t('engine.productivity.label')}</div>
          <div style={{marginTop: 18, fontFamily: serif, fontStyle: 'italic', fontSize: 31, color: paper}}>{t('engine.productivity.note')}</div>
        </div>
        <div style={{fontFamily: sans, fontSize: 110, lineHeight: .8, fontWeight: 820, letterSpacing: '-.07em', color: ice}}>{t('engine.productivity.value')}</div>
      </div>
      <div style={{position: 'absolute', left: 58, right: 58, bottom: 112, fontFamily: serif, fontSize: 27, lineHeight: 1.35, color: paper, opacity: caveat}}>{t('engine.caveat')}</div>
      <SourceLine>{t('source.bls.productivity')}</SourceLine>
    </AbsoluteFill>
  );
};

const Resolve: React.FC<{t: (key: StringKey) => string; duration: number; layoutScale: number}> = ({t, duration, layoutScale}) => {
  const frame = useCurrentFrame();
  const drift = p(frame, 0, duration);
  const empty = p(frame, 75, 150, Easing.inOut(Easing.cubic));
  const freeze = p(frame, 112, 228, Easing.inOut(Easing.cubic));
  const verdict = p(frame, 176, 242, Easing.out(Easing.cubic));
  const watch = p(frame, 236, 282, Easing.out(Easing.quad));
  return (
    <AbsoluteFill style={{opacity: beatOpacity(frame, duration, 12), background: ink, color: paper}}>
      <AssetVideo
        src="assets/documentary/office_workers_pexels_6549254.mp4"
        startFrom={360}
        opacity={1 - empty}
        scale={1.18 + drift * .06}
        x={-85 + drift * 45}
        objectPosition="52% 50%"
        filter={`saturate(${.56 - freeze * .42}) brightness(${.48 - freeze * .12}) contrast(1.16)`}
      />
      <AssetVideo
        src="assets/documentary/empty_office_pexels_7844843.mp4"
        startFrom={120}
        opacity={empty}
        scale={1.15 + drift * .035}
        x={-70}
        filter={`saturate(${.44 - freeze * .34}) brightness(${.42 - freeze * .1}) contrast(1.18)`}
      />
      <AbsoluteFill style={{background: `linear-gradient(180deg,rgba(4,10,13,.5),rgba(4,10,13,${.66 + freeze * .2}) 58%,rgba(4,10,13,.96))`}} />
      <BrandRail t={t} />
      <IllustrativeTag t={t} />
      <div style={{position: 'absolute', left: 58, right: 58, top: 450, opacity: 1 - verdict * .72, transform: `translateY(${-freeze * 34}px)`}}>
        <div style={{fontFamily: sans, fontSize: 38 * layoutScale, fontWeight: 800, letterSpacing: '.055em', lineHeight: 1.16, color: cyan}}>{t('resolve.motion')}</div>
        <div style={{marginTop: 29, fontFamily: serif, fontSize: 82 * layoutScale, fontWeight: 600, lineHeight: .98, letterSpacing: '-.045em', color: paper}}>{t('resolve.stasis')}</div>
      </div>
      <div style={{position: 'absolute', inset: 0, pointerEvents: 'none', opacity: freeze}}>
        <div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: `${freeze * 18}%`, background: 'linear-gradient(90deg,rgba(135,195,208,.3),rgba(135,195,208,.03))', borderRight: '1px solid rgba(158,199,209,.48)'}} />
        <div style={{position: 'absolute', right: 0, top: 0, bottom: 0, width: `${freeze * 18}%`, background: 'linear-gradient(270deg,rgba(135,195,208,.3),rgba(135,195,208,.03))', borderLeft: '1px solid rgba(158,199,209,.48)'}} />
        {[0, 1, 2, 3, 4].map((line) => (
          <div key={line} style={{position: 'absolute', left: 110 + line * 205, top: 230 + (line % 2) * 110, width: 1, height: 1360, background: 'linear-gradient(180deg,transparent,rgba(158,199,209,.52),transparent)', transform: `rotate(${line % 2 ? 6 : -7}deg) scaleY(${freeze})`}} />
        ))}
      </div>
      <div style={{position: 'absolute', left: 54, right: 54, top: 770, opacity: verdict, textAlign: 'center'}}>
        <div style={{fontFamily: sans, fontSize: 24, fontWeight: 800, letterSpacing: '.12em', color: paper}}>{t('resolve.notBreak')}</div>
        <div style={{width: 80, height: 3, background: copper, margin: '34px auto'}} />
        <div style={{whiteSpace: 'pre-line', fontFamily: sans, fontSize: 68 * layoutScale, fontWeight: 820, lineHeight: .98, letterSpacing: '-.05em', color: paper}}>{t('resolve.freeze')}</div>
        <div style={{marginTop: 42, fontFamily: serif, fontSize: 34 * layoutScale, lineHeight: 1.18, color: ice, opacity: watch}}>{t('resolve.watch')}</div>
      </div>
      <div style={{position: 'absolute', left: 54, right: 54, bottom: 190, height: 1, background: `linear-gradient(90deg,transparent,${ice},transparent)`, transform: `scaleX(${watch})`}} />
      <SourceLine>{t('brand.slug')} · {t('source.analysis')}</SourceLine>
    </AbsoluteFill>
  );
};

const CaptionRail: React.FC<{
  t: (key: StringKey) => string;
  locale: Locale;
}> = ({t, locale}) => {
  const frame = useCurrentFrame();
  const cue = captionCuesFor(locale).find((candidate) => frame >= candidate.from && frame < candidate.to);
  if (!cue) return null;
  const opacity = Math.min(p(frame, cue.from, cue.from + 8), 1 - p(frame, cue.to - 8, cue.to));
  const content = t(cue.key as StringKey);
  const emphasisIndex = cue.emphasis ? content.toLocaleLowerCase().indexOf(cue.emphasis.toLocaleLowerCase()) : -1;
  const before = emphasisIndex >= 0 ? content.slice(0, emphasisIndex) : content;
  const emphasized = emphasisIndex >= 0 && cue.emphasis ? content.slice(emphasisIndex, emphasisIndex + cue.emphasis.length) : '';
  const after = emphasisIndex >= 0 && cue.emphasis ? content.slice(emphasisIndex + cue.emphasis.length) : '';
  const layout = localeLayout[locale];
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: 74,
        zIndex: 100,
        padding: '105px 58px 48px',
        background: 'linear-gradient(180deg,transparent,rgba(3,8,11,.9) 66%)',
        opacity,
        pointerEvents: 'none',
      }}
    >
      <div style={{width: 44, height: 4, marginBottom: 17, background: cyan}} />
      <div
        style={{
          maxWidth: layout.captionWidth,
          fontFamily: sans,
          fontSize: 36 * layout.fontScale,
          fontWeight: 720,
          letterSpacing: '-.018em',
          lineHeight: 1.18,
          color: paper,
          textShadow: '0 2px 14px rgba(0,0,0,.78)',
        }}
      >
        {before}
        {emphasized ? <span style={{color: cyan}}>{emphasized}</span> : null}
        {after}
      </div>
    </div>
  );
};

export const FrozenWithoutBreakingShort: React.FC<ShortProps> = ({
  locale,
  burnedCaptions,
  narrationSrc,
  narrationEnabled,
}) => {
  const strings = stringsFor(locale);
  const layout = localeLayout[locale];
  const t = (key: StringKey) => strings[key];
  const {width, height} = useVideoConfig();
  return (
    <AbsoluteFill
      style={{
        width,
        height,
        overflow: 'hidden',
        background: ink,
        color: paper,
        fontFamily: sans,
      }}
    >
      <Sequence from={beats.hook.from} durationInFrames={beats.hook.duration} premountFor={30}>
        <Hook t={t} duration={beats.hook.duration} />
      </Sequence>
      <Sequence from={beats.paradox.from} durationInFrames={beats.paradox.duration} premountFor={30}>
        <Paradox t={t} duration={beats.paradox.duration} />
      </Sequence>
      <Sequence from={beats.arithmetic.from} durationInFrames={beats.arithmetic.duration} premountFor={30}>
        <Arithmetic t={t} duration={beats.arithmetic.duration} />
      </Sequence>
      <Sequence from={beats.doors.from} durationInFrames={beats.doors.duration} premountFor={30}>
        <Doors t={t} duration={beats.doors.duration} />
      </Sequence>
      <Sequence from={beats.engine.from} durationInFrames={beats.engine.duration} premountFor={30}>
        <Engine t={t} duration={beats.engine.duration} />
      </Sequence>
      <Sequence from={beats.resolve.from} durationInFrames={beats.resolve.duration} premountFor={30}>
        <Resolve t={t} duration={beats.resolve.duration} layoutScale={layout.fontScale} />
      </Sequence>
      {narrationEnabled ? <Audio src={staticFile(narrationSrc)} volume={1} /> : null}
      {burnedCaptions ? <CaptionRail t={t} locale={locale} /> : null}
      <Grain />
      <AbsoluteFill
        style={{
          pointerEvents: 'none',
          boxShadow: 'inset 0 0 190px rgba(0,0,0,.42)',
          border: '1px solid rgba(242,239,231,.035)',
        }}
      />
    </AbsoluteFill>
  );
};
