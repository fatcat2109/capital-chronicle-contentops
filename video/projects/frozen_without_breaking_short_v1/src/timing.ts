import {localizedCaptionCues} from './generated_caption_timings';
import type {Locale} from './strings';

export const FPS = 30;
export const DURATION_IN_FRAMES = 1740;

export const beats = {
  hook: {from: 0, duration: 135},
  paradox: {from: 120, duration: 225},
  arithmetic: {from: 330, duration: 360},
  doors: {from: 675, duration: 435},
  engine: {from: 1095, duration: 345},
  resolve: {from: 1425, duration: 315},
} as const;

export type CaptionCue = {
  from: number;
  to: number;
  key: string;
  emphasis?: string;
};

export const captionCues: CaptionCue[] = [
  {from: 0, to: 132, key: 'caption.01', emphasis: 'fall'},
  {from: 132, to: 310, key: 'caption.02', emphasis: '23,000'},
  {from: 310, to: 535, key: 'caption.03', emphasis: 'arithmetic'},
  {from: 535, to: 682, key: 'caption.04', emphasis: '4.1 percent'},
  {from: 682, to: 920, key: 'caption.05', emphasis: 'doors'},
  {from: 920, to: 1058, key: 'caption.06', emphasis: 'Low hire'},
  {from: 1058, to: 1248, key: 'caption.07', emphasis: '3.9 percent'},
  {from: 1248, to: 1455, key: 'caption.08', emphasis: '0.2 percent'},
  {from: 1455, to: 1575, key: 'caption.09', emphasis: 'workers can’t'},
  {from: 1575, to: 1740, key: 'caption.10', emphasis: 'freeze'},
];

export const captionCuesFor = (locale: Locale): CaptionCue[] =>
  localizedCaptionCues[locale] ?? captionCues;
