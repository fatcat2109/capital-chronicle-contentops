import React from 'react';
import {Composition} from 'remotion';
import {Scene} from './scene';
import type {SceneJob} from './types';

const fallback: SceneJob = {
  scene_id: 'fallback', chapter_id: 'fallback', primitive: 'COLD_OPEN', aspect: 'landscape',
  width: 1280, height: 720, fps: 24, duration_in_frames: 120, title: 'Capital Chronicle',
  source_label: 'Governed evidence', captions: [], narration_asset: '',
};

export const Root: React.FC = () => (
  <Composition
    id="Tier2V2Scene"
    component={Scene}
    durationInFrames={120}
    fps={24}
    width={1280}
    height={720}
    defaultProps={{job: fallback}}
    calculateMetadata={({props}) => {
      const job = (props as {job: SceneJob}).job;
      return {durationInFrames: job.duration_in_frames, fps: job.fps, width: job.width, height: job.height, props};
    }}
  />
);
