import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {easing, easeProgress, formatValue, palette, safeZone, timing, typeface} from '../motion/motionSystem';
import type {SceneJob} from '../program/types';
import {AssetImage, Headline, Kicker, LineChart} from './scaffold';

const ContentRegion: React.FC<{job: SceneJob; children: React.ReactNode; style?: React.CSSProperties}> = ({job, children, style}) => {
  const sz = safeZone(job.aspect);
  return (
    <div
      style={{
        position: 'absolute',
        left: job.width * sz.x,
        right: job.width * sz.x,
        top: job.height * (sz.top + 0.045),
        bottom: job.height * (sz.bottom + sz.captionBand),
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export const TitleOpening: React.FC<{job: SceneJob}> = ({job}) => {
  const frame = useCurrentFrame();
  const rule = easeProgress(frame, 14, 24, easing.inOut);
  return (
    <ContentRegion job={job} style={{justifyContent: 'center'}}>
      <Kicker job={job} />
      <Headline job={job} size={job.height * (job.aspect === 'vertical' ? 0.064 : 0.075)} />
      {job.subtitle ? (
        <p style={{fontSize: job.height * 0.03, color: palette.inkMuted, margin: `${job.height * 0.02}px 0 0`, maxWidth: '85%', lineHeight: 1.4, opacity: easeProgress(frame, 18, 20, easing.out)}}>
          {job.subtitle}
        </p>
      ) : null}
      <div style={{width: `${rule * 34}%`, height: 2, background: palette.accent, marginTop: job.height * 0.03}} />
    </ContentRegion>
  );
};

export const ChapterCard: React.FC<{job: SceneJob}> = ({job}) => {
  const frame = useCurrentFrame();
  const numIn = easeProgress(frame, 8, 22, easing.out);
  return (
    <ContentRegion job={job} style={{justifyContent: 'center'}}>
      <Kicker job={job} />
      <div style={{display: 'flex', alignItems: 'baseline', gap: job.width * 0.012, opacity: numIn}}>
        <span style={{fontFamily: typeface.serif, fontSize: job.height * 0.16, color: palette.accent, lineHeight: 1}}>{(job.chapter_label || 'Ch.').replace('Chapter', 'Ch.')}</span>
      </div>
      <Headline job={job} delay={14} />
      {job.subtitle ? <p style={{fontSize: job.height * 0.028, color: palette.inkMuted, marginTop: job.height * 0.018, lineHeight: 1.4}}>{job.subtitle}</p> : null}
    </ContentRegion>
  );
};

export const NumberCallout: React.FC<{job: SceneJob}> = ({job}) => {
  const frame = useCurrentFrame();
  const items = job.numbers ?? [];
  const primary = items.find((i) => i.emphasis) ?? items[0];
  const rest = items.filter((i) => i !== primary);
  const count = easeProgress(frame, 10, 26, easing.out);
  if (!primary) return null;
  const numericValue = typeof primary.value === 'number' ? primary.value : Number(primary.value);
  const animated = Number.isFinite(numericValue) ? numericValue * count : primary.value;
  return (
    <ContentRegion job={job} style={{justifyContent: 'center', alignItems: job.aspect === 'vertical' ? 'center' : 'flex-start'}}>
      <Kicker job={job} />
      <Headline job={job} size={job.height * 0.045} />
      <div style={{display: 'flex', flexDirection: 'column', gap: job.height * 0.012, marginTop: job.height * 0.03}}>
        <div style={{display: 'flex', alignItems: 'baseline', gap: job.width * 0.01}}>
          <span style={{fontFamily: typeface.serif, fontSize: job.height * (job.aspect === 'vertical' ? 0.15 : 0.13), color: palette.accent, lineHeight: 1}}>
            {formatValue(animated, primary.unit)}
          </span>
          {primary.delta ? <span style={{fontSize: job.height * 0.035, color: palette.inkMuted}}>{primary.delta}</span> : null}
        </div>
        <span style={{fontSize: job.height * 0.028, color: palette.inkMuted}}>{primary.label}</span>
      </div>
      {rest.length ? (
        <div style={{display: 'flex', gap: job.width * 0.02, marginTop: job.height * 0.035, flexWrap: 'wrap'}}>
          {rest.map((it, i) => {
            const t = easeProgress(frame, 24 + i * timing.staggerFrames, 18, easing.out);
            return (
              <div key={i} style={{border: `1px solid ${palette.panelLine}`, background: palette.safe, padding: `${job.height * 0.012}px ${job.width * 0.012}px`, opacity: t, transform: `translateY(${(1 - t) * 8}px)`}}>
                <div style={{fontSize: job.height * 0.03, color: palette.ink, fontFamily: typeface.serif}}>{formatValue(it.value, it.unit)}</div>
                <div style={{fontSize: job.height * 0.02, color: palette.inkFaint, marginTop: 2}}>{it.label}</div>
              </div>
            );
          })}
        </div>
      ) : null}
    </ContentRegion>
  );
};

export const ChartScene: React.FC<{job: SceneJob}> = ({job}) => {
  const vertical = job.aspect === 'vertical';
  const sz = safeZone(job.aspect);
  const boxW = job.width * (1 - sz.x * 2);
  const boxH = job.height * (vertical ? 0.36 : 0.5);
  const hasSeries = !!job.series?.length;
  const assetW = vertical ? boxW : (hasSeries ? boxW * 0.62 : boxW);
  return (
    <ContentRegion job={job}>
      <div>
        <Kicker job={job} />
        <Headline job={job} size={job.height * 0.044} />
      </div>
      <div style={{flex: 1, display: 'flex', flexDirection: vertical ? 'column' : 'row', alignItems: 'center', gap: job.width * 0.02}}>
        {job.asset?.path ? (
          <div style={{position: 'relative', width: assetW, height: boxH}}>
            <AssetImage job={job} box={{w: assetW, h: boxH}} />
          </div>
        ) : null}
        {hasSeries ? (
          <div style={{width: vertical ? boxW : (job.asset?.path ? boxW * 0.36 : boxW), height: boxH}}>
            <LineChart job={job} box={{w: vertical ? boxW : (job.asset?.path ? boxW * 0.36 : boxW), h: boxH}} />
          </div>
        ) : null}
      </div>
      <NumberStrip job={job} />
    </ContentRegion>
  );
};

const NumberStrip: React.FC<{job: SceneJob}> = ({job}) => {
  const frame = useCurrentFrame();
  const items = job.numbers ?? [];
  if (!items.length) return null;
  return (
    <div style={{display: 'flex', gap: job.width * 0.012, flexWrap: 'wrap'}}>
      {items.slice(0, 4).map((it, i) => {
        const t = easeProgress(frame, 20 + i * timing.staggerFrames, 16, easing.out);
        return (
          <div key={i} style={{flex: '1 1 auto', minWidth: job.width * 0.14, background: palette.safe, border: `1px solid ${palette.panelLine}`, padding: `${job.height * 0.01}px ${job.width * 0.01}px`, opacity: t}}>
            <div style={{fontSize: job.height * 0.028, fontFamily: typeface.serif, color: palette.ink}}>{formatValue(it.value, it.unit)}</div>
            <div style={{fontSize: job.height * 0.018, color: palette.inkFaint}}>{it.label}{it.delta ? ` · ${it.delta}` : ''}</div>
          </div>
        );
      })}
    </div>
  );
};

export const DocumentScene: React.FC<{job: SceneJob}> = ({job}) => {
  const frame = useCurrentFrame();
  const vertical = job.aspect === 'vertical';
  const sz = safeZone(job.aspect);
  const docW = job.width * (vertical ? (1 - sz.x * 2) : 0.5);
  const docH = job.height * (vertical ? 0.32 : 0.5);
  return (
    <ContentRegion job={job}>
      <div>
        <Kicker job={job} />
        <Headline job={job} size={job.height * 0.042} />
      </div>
      <div style={{flex: 1, display: 'flex', flexDirection: vertical ? 'column' : 'row', alignItems: 'center', gap: job.width * 0.025}}>
        <div style={{position: 'relative', width: docW, height: docH}}>
          <AssetImage job={job} box={{w: docW, h: docH}} />
        </div>
        <div style={{flex: 1, display: 'flex', flexDirection: 'column', gap: job.height * 0.016}}>
          {(job.text_blocks ?? []).slice(0, 3).map((b, i) => {
            const t = easeProgress(frame, 18 + i * 10, 18, easing.out);
            return (
              <div key={i} style={{borderLeft: `3px solid ${palette.accent}`, paddingLeft: job.width * 0.012, opacity: t}}>
                {b.heading ? <div style={{fontSize: job.height * 0.024, color: palette.accentSoft, marginBottom: 3}}>{b.heading}</div> : null}
                {b.body ? <div style={{fontSize: job.height * 0.024, color: palette.inkMuted, lineHeight: 1.35}}>{b.body}</div> : null}
              </div>
            );
          })}
        </div>
      </div>
      <NumberStrip job={job} />
    </ContentRegion>
  );
};

// small helper so the stagger uses the current frame internally via a proxy
function jobStartPad(base: number): number {
  return base;
}

export const ComparisonScene: React.FC<{job: SceneJob}> = ({job}) => {
  const frame = useCurrentFrame();
  const items = job.numbers ?? [];
  return (
    <ContentRegion job={job}>
      <div>
        <Kicker job={job} />
        <Headline job={job} size={job.height * 0.044} />
      </div>
      <div style={{flex: 1, display: 'flex', gap: job.width * 0.02, alignItems: 'stretch', flexDirection: job.aspect === 'vertical' ? 'column' : 'row'}}>
        {items.slice(0, 3).map((it, i) => {
          const t = easeProgress(frame, 14 + i * 8, 22, easing.out);
          return (
            <div key={i} style={{flex: 1, background: palette.safe, border: `1px solid ${palette.panelLine}`, borderTop: `3px solid ${palette.accent}`, padding: `${job.height * 0.02}px ${job.width * 0.014}px`, display: 'flex', flexDirection: 'column', justifyContent: 'center', opacity: t, transform: `translateY(${(1 - t) * 12}px)`}}>
              <div style={{fontSize: job.height * 0.02, color: palette.inkFaint, textTransform: 'uppercase', letterSpacing: '0.12em'}}>{it.label}</div>
              <div style={{fontSize: job.height * 0.075, fontFamily: typeface.serif, color: palette.ink, marginTop: job.height * 0.008}}>{formatValue(it.value, it.unit)}</div>
              {it.delta ? <div style={{fontSize: job.height * 0.024, color: palette.inkMuted, marginTop: job.height * 0.006}}>{it.delta}</div> : null}
            </div>
          );
        })}
      </div>
      {job.series?.length ? <div style={{height: job.height * 0.16}}><LineChart job={job} box={{w: job.width * (1 - safeZone(job.aspect).x * 2), h: job.height * 0.16}} startFrame={26} /></div> : null}
    </ContentRegion>
  );
};

export const TimelineScene: React.FC<{job: SceneJob}> = ({job}) => (
  <ContentRegion job={job}>
    <div>
      <Kicker job={job} />
      <Headline job={job} size={job.height * 0.042} />
      {job.subtitle ? <p style={{fontSize: job.height * 0.025, color: palette.inkMuted, marginTop: job.height * 0.01}}>{job.subtitle}</p> : null}
    </div>
    <div style={{flex: 1, display: 'flex', alignItems: 'center'}}>
      <div style={{width: '100%', height: job.height * (job.aspect === 'vertical' ? 0.3 : 0.4)}}>
        <LineChart job={job} box={{w: job.width * (1 - safeZone(job.aspect).x * 2), h: job.height * (job.aspect === 'vertical' ? 0.3 : 0.4)}} />
      </div>
    </div>
    <NumberStrip job={job} />
  </ContentRegion>
);

export const SourceCard: React.FC<{job: SceneJob}> = ({job}) => {
  const frame = useCurrentFrame();
  return (
    <ContentRegion job={job} style={{justifyContent: 'center'}}>
      <Kicker job={job} />
      <Headline job={job} size={job.height * 0.042} />
      <div style={{display: 'flex', flexDirection: 'column', gap: job.height * 0.014, marginTop: job.height * 0.028}}>
        {(job.text_blocks ?? []).slice(0, 4).map((b, i) => {
          const t = easeProgress(frame, 16 + i * timing.staggerFrames, 18, easing.out);
          return (
            <div key={i} style={{background: palette.safe, border: `1px solid ${palette.panelLine}`, padding: `${job.height * 0.013}px ${job.width * 0.013}px`, opacity: t}}>
              {b.heading ? <div style={{fontSize: job.height * 0.022, color: palette.accentSoft, marginBottom: 2}}>{b.heading}</div> : null}
              {b.body ? <div style={{fontSize: job.height * 0.023, color: palette.inkMuted, lineHeight: 1.35}}>{b.body}</div> : null}
            </div>
          );
        })}
      </div>
    </ContentRegion>
  );
};

export const Callout: React.FC<{job: SceneJob}> = ({job}) => {
  const frame = useCurrentFrame();
  const t = easeProgress(frame, 10, 26, easing.out);
  return (
    <ContentRegion job={job} style={{justifyContent: 'center'}}>
      <Kicker job={job} />
      <blockquote style={{fontFamily: typeface.serif, fontSize: job.height * (job.aspect === 'vertical' ? 0.045 : 0.05), lineHeight: 1.3, color: palette.ink, margin: 0, maxWidth: '90%', opacity: t, transform: `translateY(${(1 - t) * 12}px)`}}>
        {job.display_title}
      </blockquote>
      {job.subtitle ? <p style={{fontSize: job.height * 0.027, color: palette.inkMuted, marginTop: job.height * 0.02, maxWidth: '80%', lineHeight: 1.4}}>{job.subtitle}</p> : null}
    </ContentRegion>
  );
};

export const DisclaimerEndcard: React.FC<{job: SceneJob}> = ({job}) => {
  const frame = useCurrentFrame();
  const t = easeProgress(frame, 8, 24, easing.out);
  return (
    <ContentRegion job={job} style={{justifyContent: 'center', alignItems: 'center', textAlign: 'center'}}>
      <div style={{width: job.height * 0.014, height: job.height * 0.014, background: palette.accent, marginBottom: job.height * 0.02}} />
      <Headline job={job} size={job.height * 0.05} delay={4} />
      {job.subtitle ? <p style={{fontSize: job.height * 0.026, color: palette.inkMuted, marginTop: job.height * 0.018, maxWidth: '80%', lineHeight: 1.45}}>{job.subtitle}</p> : null}
      {job.disclosure ? (
        <p style={{fontSize: job.height * 0.021, color: palette.inkFaint, marginTop: job.height * 0.028, maxWidth: '70%', lineHeight: 1.4, opacity: easeProgress(frame, 26, 20, easing.out)}}>{job.disclosure}</p>
      ) : null}
    </ContentRegion>
  );
};
