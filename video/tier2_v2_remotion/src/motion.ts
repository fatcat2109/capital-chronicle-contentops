export const MOTION_SYSTEM_VERSION = 'contentops.tier2.v2.editorial-motion.1';

export const color = {
  ink: '#0b0b0c',
  paper: '#f0eee8',
  paperWarm: '#e5dfd3',
  smoke: '#a8a49b',
  white: '#fbfaf6',
  signal: '#e4402f',
  mint: '#b8f4dd',
  cobalt: '#4169e1',
  amber: '#f1b24a',
};

export const face = {
  display: '"Aptos Display", "Arial Narrow", "Helvetica Neue", Arial, sans-serif',
  editorial: 'Georgia, "Times New Roman", serif',
  mono: '"Cascadia Mono", Consolas, monospace',
};

export const clamp = (n: number) => Math.max(0, Math.min(1, n));
export const easeOut = (n: number) => 1 - Math.pow(1 - clamp(n), 3);
export const easeInOut = (n: number) => {
  const x = clamp(n);
  return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
};
export const progress = (frame: number, start: number, duration: number, ease = easeOut) =>
  ease((frame - start) / Math.max(1, duration));
export const accent = (name?: string) =>
  name === 'mint' ? color.mint : name === 'cobalt' ? color.cobalt : name === 'amber' ? color.amber : color.signal;
