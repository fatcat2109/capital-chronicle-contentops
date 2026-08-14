import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const BRAND = {
  navy: '#061019',
  ink: '#f4f1e8',
  muted: '#a8bac4',
  teal: '#43d8bd',
  copper: '#e1a05b',
  red: '#f08078',
  line: 'rgba(168,186,196,.24)',
};

export const clamp = {
  extrapolateLeft: 'clamp' as const,
  extrapolateRight: 'clamp' as const,
};

export const asset = (name: string) => staticFile(`assets/${name}`);

export const SafeText: React.FC<{
  children: React.ReactNode;
  size: number;
  lineHeight?: number;
  color?: string;
  weight?: number;
  maxWidth?: number | string;
  align?: 'left' | 'center' | 'right';
  tracking?: number;
  style?: React.CSSProperties;
}> = ({
  children,
  size,
  lineHeight = 1.04,
  color = BRAND.ink,
  weight = 800,
  maxWidth = '100%',
  align = 'left',
  tracking = -0.025,
  style,
}) => (
  <div
    style={{
      color,
      fontFamily: 'Arial, Helvetica, sans-serif',
      fontSize: size,
      lineHeight,
      fontWeight: weight,
      letterSpacing: `${tracking}em`,
      maxWidth,
      textAlign: align,
      overflowWrap: 'break-word',
      ...style,
    }}
  >
    {children}
  </div>
);

export const Eyebrow: React.FC<{
  children: React.ReactNode;
  portrait?: boolean;
  color?: string;
}> = ({children, portrait = false, color = BRAND.teal}) => (
  <div
    style={{
      color,
      fontFamily: 'Arial, Helvetica, sans-serif',
      fontSize: portrait ? 22 : 18,
      lineHeight: 1,
      fontWeight: 900,
      letterSpacing: portrait ? 3.4 : 3,
      textTransform: 'uppercase',
    }}
  >
    {children}
  </div>
);

export const SourceAttribution: React.FC<{
  children: React.ReactNode;
  portrait?: boolean;
  dark?: boolean;
}> = ({children, portrait = false, dark = true}) => (
  <div
    data-source-zone="true"
    style={{
      position: 'absolute',
      left: portrait ? 48 : 64,
      right: portrait ? 48 : 64,
      bottom: portrait ? 38 : 26,
      minHeight: portrait ? 34 : 28,
      color: dark ? '#d9e2e7' : BRAND.navy,
      fontFamily: 'Arial, Helvetica, sans-serif',
      fontSize: portrait ? 24 : 20,
      lineHeight: 1.25,
      fontWeight: 600,
      letterSpacing: 0.15,
      textShadow: dark ? '0 2px 8px rgba(0,0,0,.94)' : 'none',
      zIndex: 80,
    }}
  >
    {children}
  </div>
);

export const EditorialCaption: React.FC<{
  children: React.ReactNode;
  portrait?: boolean;
  visible: boolean;
}> = ({children, portrait = false, visible}) =>
  visible ? (
    <div
      data-caption-zone="true"
      style={{
        position: 'absolute',
        left: portrait ? 54 : 220,
        right: portrait ? 54 : 220,
        bottom: portrait ? 138 : 82,
        padding: portrait ? '15px 20px' : '12px 18px',
        background: 'rgba(4,12,18,.92)',
        borderLeft: `5px solid ${BRAND.teal}`,
        color: BRAND.ink,
        fontFamily: 'Arial, Helvetica, sans-serif',
        fontSize: portrait ? 30 : 25,
        lineHeight: 1.22,
        fontWeight: 700,
        zIndex: 90,
      }}
    >
      {children}
    </div>
  ) : null;

export const DocumentaryImage: React.FC<{
  name: string;
  fit?: 'cover' | 'contain';
  position?: string;
  scaleFrom?: number;
  scaleTo?: number;
  style?: React.CSSProperties;
}> = ({name, fit = 'cover', position = 'center', scaleFrom = 1, scaleTo = 1.045, style}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const scale = interpolate(frame, [0, durationInFrames], [scaleFrom, scaleTo], clamp);
  return (
    <Img
      data-render-asset={name}
      src={asset(name)}
      style={{
        width: '100%',
        height: '100%',
        objectFit: fit,
        objectPosition: position,
        transform: `scale(${scale})`,
        ...style,
      }}
    />
  );
};

export const SceneIn: React.FC<{
  children: React.ReactNode;
  delay?: number;
  distance?: number;
  axis?: 'x' | 'y';
  style?: React.CSSProperties;
}> = ({children, delay = 0, distance = 28, axis = 'y', style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const progress = spring({frame: frame - delay, fps, config: {damping: 20, stiffness: 145, mass: .85}});
  const transform = axis === 'x'
    ? `translateX(${(1 - progress) * distance}px)`
    : `translateY(${(1 - progress) * distance}px)`;
  return <div style={{opacity: progress, transform, ...style}}>{children}</div>;
};

export const BrandBug: React.FC<{portrait?: boolean}> = ({portrait = false}) => (
  <div
    style={{
      position: 'absolute',
      top: portrait ? 42 : 34,
      right: portrait ? 48 : 60,
      color: BRAND.ink,
      fontFamily: 'Arial, Helvetica, sans-serif',
      fontSize: portrait ? 18 : 16,
      fontWeight: 900,
      letterSpacing: 2.2,
      zIndex: 70,
    }}
  >
    CAPITAL <span style={{color: BRAND.teal}}>CHRONICLE</span>
  </div>
);

export const DarkFrame: React.FC<{
  children: React.ReactNode;
  portrait?: boolean;
  padding?: string;
  style?: React.CSSProperties;
}> = ({children, portrait = false, padding, style}) => (
  <AbsoluteFill
    style={{
      overflow: 'hidden',
      background: BRAND.navy,
      padding: padding ?? (portrait ? '76px 54px 118px' : '56px 70px 74px'),
      ...style,
    }}
  >
    {children}
  </AbsoluteFill>
);

export const Rule: React.FC<{width?: number | string; color?: string}> = ({width = 132, color = BRAND.teal}) => (
  <div style={{height: 4, width, background: color, marginTop: 20}} />
);

export const NumberTag: React.FC<{children: React.ReactNode; color?: string}> = ({children, color = BRAND.teal}) => (
  <div
    style={{
      width: 50,
      height: 50,
      borderRadius: 999,
      display: 'grid',
      placeItems: 'center',
      background: color,
      color: BRAND.navy,
      fontFamily: 'Arial, Helvetica, sans-serif',
      fontSize: 21,
      lineHeight: 1,
      fontWeight: 950,
      flex: '0 0 auto',
    }}
  >
    {children}
  </div>
);

export const GridTexture: React.FC = () => (
  <AbsoluteFill
    style={{
      opacity: .16,
      backgroundImage:
        'linear-gradient(rgba(67,216,189,.18) 1px, transparent 1px), linear-gradient(90deg, rgba(67,216,189,.18) 1px, transparent 1px)',
      backgroundSize: '56px 56px',
      maskImage: 'linear-gradient(180deg, transparent, black 25%, black 70%, transparent)',
    }}
  />
);
