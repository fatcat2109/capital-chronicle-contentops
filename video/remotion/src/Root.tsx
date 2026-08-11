import React from 'react';
import {Composition} from 'remotion';
import {SceneRenderer} from './scenes/SceneRenderer';
import type {SceneJob} from './program/types';

const defaultScene: SceneJob = {
  scene_id: 'default',
  chapter_id: 'default-chapter',
  visual_primitive: 'TITLE_OPENING',
  aspect: 'landscape',
  width: 1920,
  height: 1080,
  fps: 30,
  duration_in_frames: 150,
  narration_seconds: 5,
  display_title: 'Capital Chronicle',
  source_label: 'Source: governed evidence. Capital Chronicle render.',
  captions: [],
  rights_synthetic: false,
};

export const Root: React.FC = () => {
  return (
    <Composition
      id="Scene"
      component={SceneRenderer}
      durationInFrames={150}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{job: defaultScene}}
      calculateMetadata={({props}) => {
        const job = (props as {job: SceneJob}).job;
        return {
          durationInFrames: Math.max(1, job.duration_in_frames),
          fps: job.fps,
          width: job.width,
          height: job.height,
          props,
        };
      }}
    />
  );
};
