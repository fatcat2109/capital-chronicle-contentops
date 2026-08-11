/**
 * Capital Chronicle — institutional financial-news motion system.
 *
 * This is the single versioned visual authority consumed by every scene
 * primitive. Restrained, evidence-first, contemporary financial-news design.
 * The version string participates in scene cache identity on the Python side.
 */
export const MOTION_SYSTEM_VERSION = 'contentops.financial_news_motion.b3';

export const palette = {
  background: '#0b1220',
  backgroundSoft: '#101a2c',
  panel: '#14213a',
  panelLine: 'rgba(214,168,79,0.22)',
  ink: '#f5f1e6',
  inkMuted: '#b9c2d2',
  inkFaint: '#8894a8',
  accent: '#d6a84f',
  accentSoft: 'rgba(214,168,79,0.85)',
  positive: '#4fae7a',
  negative: '#c46a5a',
  safe: 'rgba(245,241,230,0.08)',
} as const;

export const typeface = {
  serif: 'Georgia, "Times New Roman", "Palatino Linotype", serif',
  sans: '"Segoe UI", "Helvetica Neue", Arial, Helvetica, sans-serif',
} as const;

/** Safe-zone margins as a fraction of the frame for 16:9 and 9:16. */
export const safeZone = (aspect: 'landscape' | 'vertical') =>
  aspect === 'landscape'
    ? {x: 0.06, top: 0.07, bottom: 0.10, captionBand: 0.135}
    : {x: 0.07, top: 0.09, bottom: 0.16, captionBand: 0.20};

export const easing = {
  /** Slow editorial ease used for entrances; no bounce, no overshoot. */
  out: (t: number) => 1 - Math.pow(1 - clamp01(t), 3),
  inOut: (t: number) => {
    const x = clamp01(t);
    return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
  },
};

export const timing = {
  /** Frames for a standard element entrance. */
  entranceFrames: 22,
  /** Stagger between successive list rows. */
  staggerFrames: 7,
  /** Frames reserved as a quiet tail after narration ends (transition zone). */
  transitionTailSeconds: 1.0,
};

export function clamp01(t: number): number {
  return Math.min(1, Math.max(0, t));
}

/** Linear interpolation with an easing applied over a frame window. */
export function easeProgress(frame: number, start: number, duration: number, ease: (t: number) => number): number {
  if (duration <= 0) return frame >= start ? 1 : 0;
  return ease(clamp01((frame - start) / duration));
}

/** Format a governed numeric value without inventing precision. */
export function formatValue(value: number | string | null, unit?: string): string {
  if (value === null || value === undefined || value === '') return '—';
  const numeric = typeof value === 'number' ? value : Number(value);
  if (Number.isFinite(numeric)) {
    const abs = Math.abs(numeric);
    const decimals = Number.isInteger(numeric) && abs < 1000 ? 0 : Math.abs(numeric) >= 100 ? 1 : 2;
    const text = numeric.toFixed(decimals);
    return unit === 'basis_points' ? `${text.replace(/\.0+$/, '')} bp` : unit === 'percent' ? `${text}%` : `${text}${unit ? ` ${unit}` : ''}`;
  }
  return `${String(value)}${unit ? ` ${unit}` : ''}`;
}


