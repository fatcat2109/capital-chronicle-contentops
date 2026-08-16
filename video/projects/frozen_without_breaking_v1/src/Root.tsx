import React from 'react';
import {Composition} from 'remotion';
import {Film} from './Film';
import {Chapter01} from './chapters/Chapter01';
import {Chapter02} from './chapters/Chapter02';
import {Chapter03} from './chapters/Chapter03';
import {Chapter04} from './chapters/Chapter04';
import {Chapter05} from './chapters/Chapter05';
import {Chapter06} from './chapters/Chapter06';
import {Chapter07} from './chapters/Chapter07';
import {FPS, chapters, totalDurationInFrames} from './timing';

const chapterComponents = [
  Chapter01,
  Chapter02,
  Chapter03,
  Chapter04,
  Chapter05,
  Chapter06,
  Chapter07,
];

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="FrozenWithoutBreaking"
      component={Film}
      durationInFrames={totalDurationInFrames}
      fps={FPS}
      width={1920}
      height={1080}
    />
    {chapters.map((chapter, index) => {
      const Component = chapterComponents[index];
      return (
        <Composition
          key={chapter.id}
          id={chapter.id}
          component={Component}
          durationInFrames={chapter.durationInFrames}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{durationInFrames: chapter.durationInFrames}}
        />
      );
    })}
  </>
);
