// Inert build placeholder. The proof runner replaces this file mechanically with imports
// and duration constants bound to accepted GPT-5.6-authored source receipts.
import React from 'react';
import type {VariantProps} from '../types';

const NotAuthored: React.FC<VariantProps> = () => {
  throw new Error('GPT56_AUTHORED_COMPOSITION_NOT_PERSISTED');
};

export const ShortVideo = NotAuthored;
export const MidformVideo = NotAuthored;
export const shortDurationFrames = 1350;
export const midformDurationFrames = 2700;
export const authoredSegments: Array<{
  id: string;
  component: React.FC<VariantProps>;
  durationInFrames: number;
  width: number;
  height: number;
}> = [];
