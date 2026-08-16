import type {ChapterDefinition} from './types';

export const FPS = 30;

export const chapters: ChapterDefinition[] = [
  {
    id: 'Chapter01',
    title: 'The Nine-Day Gap',
    durationInFrames: 3615,
    narration: 'assets/audio/narration/chapter_01.wav',
    soundBed: 'assets/audio/sound/chapter_01_bed.m4a',
  },
  {
    id: 'Chapter02',
    title: 'The Rate That Fell Without Hiring',
    durationInFrames: 3614,
    narration: 'assets/audio/narration/chapter_02.wav',
    soundBed: 'assets/audio/sound/chapter_02_bed.m4a',
  },
  {
    id: 'Chapter03',
    title: 'The Revolving Door Stopped',
    durationInFrames: 3866,
    narration: 'assets/audio/narration/chapter_03.wav',
    soundBed: 'assets/audio/sound/chapter_03_bed.m4a',
  },
  {
    id: 'Chapter04',
    title: 'One Sector Holds the Ceiling',
    durationInFrames: 3123,
    narration: 'assets/audio/narration/chapter_04.wav',
    soundBed: 'assets/audio/sound/chapter_04_bed.m4a',
  },
  {
    id: 'Chapter05',
    title: 'The Machine Keeps Running',
    durationInFrames: 3244,
    narration: 'assets/audio/narration/chapter_05.wav',
    soundBed: 'assets/audio/sound/chapter_05_bed.m4a',
  },
  {
    id: 'Chapter06',
    title: 'The Missing Share',
    durationInFrames: 3191,
    narration: 'assets/audio/narration/chapter_06.wav',
    soundBed: 'assets/audio/sound/chapter_06_bed.m4a',
  },
  {
    id: 'Chapter07',
    title: 'No Easy Exit',
    durationInFrames: 4798,
    narration: 'assets/audio/narration/chapter_07.wav',
    soundBed: 'assets/audio/sound/chapter_07_bed.m4a',
  },
];

export const totalDurationInFrames = chapters.reduce(
  (total, chapter) => total + chapter.durationInFrames,
  0,
);
