import React from 'react';
import {Composition} from 'remotion';
import {FrozenWithoutBreakingShort, type ShortProps} from './Short';
import {DURATION_IN_FRAMES, FPS} from './timing';

const common = {
  component: FrozenWithoutBreakingShort,
  durationInFrames: DURATION_IN_FRAMES,
  fps: FPS,
  width: 1080,
  height: 1920,
} as const;

const clean: ShortProps = {
  locale: 'en',
  burnedCaptions: false,
  narrationSrc: 'assets/audio/narration/frozen_without_breaking_short_en.wav',
  narrationEnabled: true,
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="FrozenWithoutBreakingShortClean"
      {...common}
      defaultProps={clean}
    />
    <Composition
      id="FrozenWithoutBreakingShortBurnedCaptions"
      {...common}
      defaultProps={{...clean, burnedCaptions: true}}
    />
  </>
);
