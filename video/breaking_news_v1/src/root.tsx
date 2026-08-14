import React from 'react';
import {CalculateMetadataFunction, Composition} from 'remotion';
import {BreakingRetailSales, BreakingProps, defaults} from './generated/retailBreaking';

const calculateMetadata: CalculateMetadataFunction<BreakingProps> = ({props}) => ({
  durationInFrames: props.segments.reduce((total, segment) => total + segment.frames, 0),
  props,
});

export const Root: React.FC = () => <Composition
  id="BreakingRetailSales"
  component={BreakingRetailSales}
  durationInFrames={1800}
  fps={30}
  width={1080}
  height={1920}
  defaultProps={defaults}
  calculateMetadata={calculateMetadata}
/>;
