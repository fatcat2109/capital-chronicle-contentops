import React from 'react';
import {Composition} from 'remotion';
import {
  MidformVideo,
  ShortVideo,
  authoredSegments,
  midformDurationFrames,
  shortDurationFrames,
} from './generated';

export const ConcreteFirstRoot: React.FC = () => (
  <>
    <Composition
      id="ConcreteFirstShort"
      component={ShortVideo}
      durationInFrames={shortDurationFrames}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{captionsVisible: true, assetBase: ''}}
    />
    <Composition
      id="ConcreteFirstMidform"
      component={MidformVideo}
      durationInFrames={midformDurationFrames}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{captionsVisible: true, assetBase: ''}}
    />
    {authoredSegments.map((segment) => (
      <Composition
        key={segment.id}
        id={segment.id}
        component={segment.component}
        durationInFrames={segment.durationInFrames}
        fps={30}
        width={segment.width}
        height={segment.height}
        defaultProps={{captionsVisible: true, assetBase: ''}}
      />
    ))}
  </>
);
