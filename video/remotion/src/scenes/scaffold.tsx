import React from 'react';
import {AbsoluteFill, Audio, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {easing, easeProgress, palette, safeZone, timing, typeface} from '../motion/motionSystem';
import type {SceneJob} from '../program/types';

export const Frame: React.FC<{job: SceneJob; children: React.ReactNode}> = ({job, children}) => {
  const vertical = job.aspect === 'vertical';
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(120% 120% at ${vertical ? '50% 0%' : '18% 0%'}, ${palette.backgroundSoft} 0%, ${palette.background} 55%, #070c16 100%)`,
        fontFamily: typeface.sans,
        color: palette.ink,
      }}
    >
      <div style={{position: 'absolute', inset: 0, opacity: 0.05, background: 'repeating-linear-gradient(0deg, rgba(245,241,230,0.5) 0 1px, transparent 1px 64px)'}} />
      {children}
      <TopBar job={job} />
      <SourceLabel job={job} />
      <CaptionOverlay job={job} />
      {job.narration_asset ? <Audio src={staticFile(job.narration_asset)} volume={1} /> : null}
    </AbsoluteFill>
  );
};

export const TopBar: React.FC<{job: SceneJob}> = ({job}) => {
  const frame = useCurrentFrame();
  const t = easeProgress(frame, 2, timing.entranceFrames, easing.out);
  const sz = safeZone(job.aspect);
  return (
    <div
      style={{
        position: 'absolute',
        top: job.height * 0.028,
        left: job.width * sz.x,
        right: job.width * sz.x,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        opacity: t,
        transform: `translateY(${(1 - t) * -8}px)`,
      }}
    >
      <div style={{display: 'flex', alignItems: 'center', gap: job.width * 0.008}}>
        <div style={{width: job.width * 0.012, height: job.width * 0.012, background: palette.accent}} />
        <span style={{fontFamily: typeface.sans, letterSpacing: '0.22em', fontSize: job.height * 0.021, color: palette.inkMuted, textTransform: 'uppercase'}}>
          Capital Chronicle
        </span>
      </div>
      {job.chapter_label ? (
        <span style={{fontSize: job.height * 0.019, letterSpacing: '0.18em', color: palette.inkFaint, textTransform: 'uppercase'}}>{job.chapter_label}</span>
      ) : null}
    </div>
  );
};

export const SourceLabel: React.FC<{job: SceneJob}> = ({job}) => {
  const frame = useCurrentFrame();
  const t = easeProgress(frame, 6, timing.entranceFrames, easing.out);
  const sz = safeZone(job.aspect);
  if (!job.source_label && !job.credit_line) return null;
  return (
    <div
      style={{
        position: 'absolute',
        top: job.height * 0.062,
        left: job.width * sz.x,
        right: job.width * sz.x,
        display: 'flex',
        justifyContent: 'space-between',
        gap: job.width * 0.01,
        opacity: t * 0.95,
      }}
    >
      <span style={{fontSize: job.height * 0.017, color: palette.inkFaint, lineHeight: 1.3, maxWidth: '72%'}}>{job.source_label}</span>
      {job.credit_line ? (
        <span style={{fontSize: job.height * 0.017, color: palette.inkFaint, textAlign: 'right', lineHeight: 1.3}}>{job.credit_line}</span>
      ) : null}
    </div>
  );
};

export const CaptionOverlay: React.FC<{job: SceneJob}> = ({job}) => {
  const frame = useCurrentFrame();
  const sz = safeZone(job.aspect);
  const cue = job.captions.find((c) => frame >= c.start_frame && frame < c.end_frame);
  if (!cue) return null;
  const localIn = easeProgress(frame, cue.start_frame, 6, easing.out);
  const vertical = job.aspect === 'vertical';
  return (
    <div
      style={{
        position: 'absolute',
        left: job.width * sz.x,
        right: job.width * sz.x,
        bottom: job.height * (sz.bottom + 0.004),
        display: 'flex',
        justifyContent: 'center',
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          maxWidth: vertical ? '96%' : '76%',
          maxHeight: job.height * sz.captionBand,
          overflow: 'hidden',
          background: 'rgba(7,12,22,0.82)',
          border: `1px solid ${palette.panelLine}`,
          padding: `${job.height * 0.009}px ${job.width * (vertical ? 0.03 : 0.014)}px`,
          textAlign: 'center',
          opacity: localIn,
        }}
      >
        <span style={{fontSize: job.height * (vertical ? 0.028 : 0.026), lineHeight: 1.22, color: palette.ink, fontWeight: 500}}>{cue.text}</span>
      </div>
    </div>
  );
};

export const Kicker: React.FC<{job: SceneJob; delay?: number}> = ({job, delay = 0}) => {
  const frame = useCurrentFrame();
  const t = easeProgress(frame, 4 + delay, timing.entranceFrames, easing.out);
  if (!job.kicker) return null;
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: job.width * 0.006, opacity: t, transform: `translateY(${(1 - t) * 10}px)`, marginBottom: job.height * 0.012}}>
      <div style={{width: job.height * 0.012, height: job.height * 0.012, background: palette.accent}} />
      <span style={{fontSize: job.height * 0.022, letterSpacing: '0.28em', textTransform: 'uppercase', color: palette.accentSoft}}>{job.kicker}</span>
    </div>
  );
};

export const Headline: React.FC<{job: SceneJob; delay?: number; size?: number; serif?: boolean}> = ({job, delay = 6, size, serif = true}) => {
  const frame = useCurrentFrame();
  const t = easeProgress(frame, delay, timing.entranceFrames + 6, easing.out);
  return (
    <h1
      style={{
        fontFamily: serif ? typeface.serif : typeface.sans,
        fontSize: size ?? job.height * (job.aspect === 'vertical' ? 0.052 : 0.058),
        lineHeight: 1.12,
        color: palette.ink,
        fontWeight: 600,
        margin: 0,
        opacity: t,
        transform: `translateY(${(1 - t) * 14}px)`,
        textWrap: 'balance',
      }}
    >
      {job.display_title}
    </h1>
  );
};

/** Deterministic polyline chart with staggered draw-in and dot markers. */
export const LineChart: React.FC<{
  job: SceneJob;
  box: {w: number; h: number};
  startFrame?: number;
}> = ({job, box, startFrame = 10}) => {
  const frame = useCurrentFrame();
  const series = job.series ?? [];
  if (!series.length) return null;
  const pad = box.h * 0.10;
  const all = series.flatMap((s) => s.points.map((p) => p.y));
  const minY = Math.min(...all);
  const maxY = Math.max(...all);
  const span = maxY - minY || 1;
  const n = Math.max(...series.map((s) => s.points.length));
  const x = (i: number) => pad + (i / Math.max(1, n - 1)) * (box.w - pad * 2);
  const y = (v: number) => pad + (1 - (v - minY) / span) * (box.h - pad * 2);

  // Restrained clip reveal: the chart wipes in over ~0.6s, no continuous zoom.
  const reveal = easeProgress(frame, startFrame, 20, easing.inOut);

  return (
    <svg width={box.w} height={box.h} viewBox={`0 0 ${box.w} ${box.h}`} style={{display: 'block', clipPath: `inset(0 ${Math.round((1 - reveal) * 100)}% 0 0)`}}>
      {[0, 0.25, 0.5, 0.75, 1].map((g) => (
        <line key={g} x1={pad} x2={box.w - pad} y1={pad + g * (box.h - pad * 2)} y2={pad + g * (box.h - pad * 2)} stroke="rgba(245,241,230,0.07)" strokeWidth={1} />
      ))}
      {series.map((s, si) => {
        const pts = s.points.map((p, i) => `${x(i)},${y(p.y)}`).join(' ');
        const color = s.color ?? palette.accent;
        return (
          <g key={si}>
            <polyline points={pts} fill="none" stroke={color} strokeWidth={Math.max(2, box.h * 0.006)} strokeLinejoin="round" strokeLinecap="round" />
            {s.points.map((p, i) => {
              const dot = easeProgress(frame, startFrame + 20 + i * 2, 8, easing.out);
              return dot > 0 ? <circle key={i} cx={x(i)} cy={y(p.y)} r={Math.max(2, box.h * 0.006) * dot} fill={color} /> : null;
            })}
          </g>
        );
      })}
      <text x={pad} y={box.h - pad * 0.25} fill={palette.inkMuted} fontSize={box.h * 0.06} fontFamily={typeface.sans}>
        {series[0]?.points[0]?.x}
      </text>
      <text x={box.w - pad} y={box.h - pad * 0.25} fill={palette.inkMuted} fontSize={box.h * 0.06} fontFamily={typeface.sans} textAnchor="end">
        {series[0]?.points[series[0].points.length - 1]?.x}
      </text>
      <text x={pad} y={pad * 0.8} fill={palette.ink} fontSize={box.h * 0.065} fontFamily={typeface.sans}>
        {formatAxis(maxY, job)}
      </text>
    </svg>
  );
};

function formatAxis(v: number, job: SceneJob): string {
  const looksPercent = job.numbers?.some((n) => n.unit === 'percent') || job.series?.length;
  return looksPercent ? `${v.toFixed(2)}%` : `${v.toFixed(2)}`;
}

export const AssetImage: React.FC<{job: SceneJob; box: {w: number; h: number; x?: number; y?: number}; delay?: number}> = ({job, box, delay = 8}) => {
  const frame = useCurrentFrame();
  const t = easeProgress(frame, delay, timing.entranceFrames + 8, easing.out);
  if (!job.asset?.path) return null;
  const src = job.asset.path.startsWith('http') || job.asset.path.startsWith('data:') ? job.asset.path : staticFile(job.asset.path);
  return (
    <div style={{position: 'absolute', left: box.x ?? 0, top: box.y ?? 0, width: box.w, height: box.h, opacity: t, transform: `scale(${0.985 + 0.015 * t})`, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <Img src={src} style={{maxWidth: '100%', maxHeight: '100%', border: `1px solid ${palette.panelLine}`, boxShadow: '0 24px 60px rgba(0,0,0,0.45)'}} />
    </div>
  );
};
