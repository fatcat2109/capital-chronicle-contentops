import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';
import {Chapter01} from './chapters/Chapter01';
import {Chapter02} from './chapters/Chapter02';
import {Chapter03} from './chapters/Chapter03';
import {Chapter04} from './chapters/Chapter04';
import {Chapter05} from './chapters/Chapter05';
import {Chapter06} from './chapters/Chapter06';
import {Chapter07} from './chapters/Chapter07';
import {chapters} from './timing';

const components = [
  Chapter01,
  Chapter02,
  Chapter03,
  Chapter04,
  Chapter05,
  Chapter06,
  Chapter07,
];

export const Film: React.FC = () => {
  let from = 0;
  return (
    <AbsoluteFill style={{background: '#081015'}}>
      {chapters.map((chapter, index) => {
        const Component = components[index];
        const currentFrom = from;
        from += chapter.durationInFrames;
        return (
          <Sequence
            key={chapter.id}
            from={currentFrom}
            durationInFrames={chapter.durationInFrames}
            premountFor={60}
          >
            <Component durationInFrames={chapter.durationInFrames} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
