import React from 'react';
import {CalculateMetadataFunction, Composition} from 'remotion';
import {HybridShort, HybridVideoProps} from './video';

const defaultProps: HybridVideoProps = {
  owner_label: 'HIGH',
  run_id: 'preview',
  audio_file: '',
  scenes: [],
};

const calculateMetadata: CalculateMetadataFunction<HybridVideoProps> = ({props}) => ({
  durationInFrames: Math.max(1, Math.round(props.scenes.reduce((sum, scene) => sum + scene.duration_seconds, 0) * 30)),
  defaultOutName: `${props.owner_label.toLowerCase()}-clean-master.mp4`,
});

export const Root: React.FC = () => (
  <Composition
    id="LaneBHybridShort"
    component={HybridShort}
    durationInFrames={1620}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={defaultProps}
    calculateMetadata={calculateMetadata}
  />
);
