import React from 'react';
import {
  AbsoluteFill,
  Easing,
  Img,
  OffthreadVideo,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const ink = '#081015';
export const paper = '#F1EEE7';
export const silver = '#AAB6BB';
export const cyan = '#77C8C2';
export const copper = '#D57A52';
export const red = '#D84A45';
export const amber = '#E8A95B';

export const sans = 'Manrope, Arial, sans-serif';
export const serif = 'Source Serif 4, Georgia, serif';

export const clamp = (value: number, low = 0, high = 1) =>
  Math.min(high, Math.max(low, value));

export const lerp = (from: number, to: number, amount: number) =>
  from + (to - from) * amount;

export const progress = (
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

export const holdFade = (
  frame: number,
  start: number,
  end: number,
  fadeFrames = 18,
) =>
  Math.min(
    progress(frame, start, start + fadeFrames, Easing.out(Easing.quad)),
    1 - progress(frame, end - fadeFrames, end, Easing.in(Easing.quad)),
  );

export const FilmGrain: React.FC<{opacity?: number}> = ({opacity = 0.11}) => {
  const frame = useCurrentFrame();
  const shift = (frame * 37) % 180;
  return (
    <AbsoluteFill
      style={{
        pointerEvents: 'none',
        opacity,
        mixBlendMode: 'soft-light',
        transform: `translate(${(shift % 7) - 3}px, ${((shift * 3) % 7) - 3}px)`,
        backgroundImage:
          'url("data:image/svg+xml,%3Csvg viewBox=%270 0 180 180%27 xmlns=%27http://www.w3.org/2000/svg%27%3E%3Cfilter id=%27n%27%3E%3CfeTurbulence type=%27fractalNoise%27 baseFrequency=%27.83%27 numOctaves=%274%27 stitchTiles=%27stitch%27/%3E%3C/filter%3E%3Crect width=%27100%25%27 height=%27100%25%27 filter=%27url(%23n)%27 opacity=%27.55%27/%3E%3C/svg%3E")',
      }}
    />
  );
};
export const Vignette: React.FC<{strength?: number}> = ({strength = 0.8}) => (
  <AbsoluteFill
    style={{
      pointerEvents: 'none',
      background: `radial-gradient(circle at 50% 44%, transparent 26%, rgba(4,9,12,${
        0.45 * strength
      }) 72%, rgba(2,5,7,${0.92 * strength}) 115%)`,
    }}
  />
);

export const SourceTag: React.FC<{
  children: React.ReactNode;
  align?: 'left' | 'right';
  color?: string;
}> = ({children, align = 'left', color = silver}) => (
  <div
    style={{
      position: 'absolute',
      left: align === 'left' ? 54 : undefined,
      right: align === 'right' ? 54 : undefined,
      bottom: 38,
      fontFamily: sans,
      fontSize: 17,
      fontWeight: 550,
      letterSpacing: '0.11em',
      textTransform: 'uppercase',
      color,
      opacity: 0.9,
    }}
  >
    {children}
  </div>
);

export const ChapterSlug: React.FC<{
  number: number;
  children: React.ReactNode;
  opacity?: number;
}> = ({number, children, opacity = 1}) => (
  <div
    style={{
      position: 'absolute',
      left: 62,
      top: 48,
      display: 'flex',
      gap: 15,
      alignItems: 'center',
      opacity,
      fontFamily: sans,
      color: paper,
      fontSize: 17,
      fontWeight: 650,
      letterSpacing: '0.16em',
      textTransform: 'uppercase',
    }}
  >
    <span style={{color: copper}}>{String(number).padStart(2, '0')}</span>
    <span style={{width: 36, height: 1, background: 'rgba(241,238,231,.35)'}} />
    <span>{children}</span>
  </div>
);

export const FullBleedVideo: React.FC<{
  src: string;
  startFrom?: number;
  endAt?: number;
  playbackRate?: number;
  opacity?: number;
  muted?: boolean;
  volume?: number | ((frame: number) => number);
  style?: React.CSSProperties;
}> = ({
  src,
  startFrom,
  endAt,
  playbackRate,
  opacity = 1,
  muted = true,
  volume,
  style,
}) => (
  <OffthreadVideo
    src={staticFile(src)}
    startFrom={startFrom}
    endAt={endAt}
    playbackRate={playbackRate}
    muted={muted}
    volume={volume}
    style={{
      width: '100%',
      height: '100%',
      objectFit: 'cover',
      opacity,
      ...style,
    }}
  />
);

export const FullBleedImage: React.FC<{
  src: string;
  opacity?: number;
  zoom?: number;
  x?: number;
  y?: number;
  style?: React.CSSProperties;
}> = ({src, opacity = 1, zoom = 1, x = 0, y = 0, style}) => (
  <Img
    src={staticFile(src)}
    style={{
      width: '100%',
      height: '100%',
      objectFit: 'cover',
      opacity,
      transform: `translate(${x}px, ${y}px) scale(${zoom})`,
      ...style,
    }}
  />
);

export const ThinRule: React.FC<{
  x: number;
  y: number;
  width: number;
  color?: string;
  opacity?: number;
}> = ({x, y, width, color = paper, opacity = 0.35}) => (
  <div
    style={{
      position: 'absolute',
      left: x,
      top: y,
      width,
      height: 1,
      background: color,
      opacity,
    }}
  />
);

export const Canvas: React.FC<{children: React.ReactNode; background?: string}> = ({
  children,
  background = ink,
}) => {
  const {width, height} = useVideoConfig();
  return (
    <AbsoluteFill
      style={{
        width,
        height,
        overflow: 'hidden',
        background,
        color: paper,
        fontFamily: sans,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
