import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';
import type {VariantProps} from '../types';
import {Motion_short_9x16_S1_CHOKEPOINT_IN_VIEW} from './short_9x16_S1_CHOKEPOINT_IN_VIEW';
import {Motion_short_9x16_S2_FROM_TRANSIT_TO_BARRELS} from './short_9x16_S2_FROM_TRANSIT_TO_BARRELS';
import {Motion_short_9x16_S3_THE_FORECAST_ON_RECORD} from './short_9x16_S3_THE_FORECAST_ON_RECORD';
import {Motion_short_9x16_S4_BEYOND_THE_BARREL} from './short_9x16_S4_BEYOND_THE_BARREL';
import {Motion_short_9x16_S5_THE_REBALANCE_TEST} from './short_9x16_S5_THE_REBALANCE_TEST';
import {Motion_midform_16x9_S1_CHOKEPOINT_IN_VIEW} from './midform_16x9_S1_CHOKEPOINT_IN_VIEW';
import {Motion_midform_16x9_S2_FROM_TRANSIT_TO_BARRELS} from './midform_16x9_S2_FROM_TRANSIT_TO_BARRELS';
import {Motion_midform_16x9_S3_THE_FORECAST_ON_RECORD} from './midform_16x9_S3_THE_FORECAST_ON_RECORD';
import {Motion_midform_16x9_S4_BEYOND_THE_BARREL} from './midform_16x9_S4_BEYOND_THE_BARREL';
import {Motion_midform_16x9_S5_THE_REBALANCE_TEST} from './midform_16x9_S5_THE_REBALANCE_TEST';

export const ShortVideo: React.FC<VariantProps> = (props) => (
  <AbsoluteFill style={{backgroundColor: '#081018'}}>
    <Sequence from={0} durationInFrames={282} name="S1_CHOKEPOINT_IN_VIEW">
      <Motion_short_9x16_S1_CHOKEPOINT_IN_VIEW {...props} />
    </Sequence>
    <Sequence from={282} durationInFrames={324} name="S2_FROM_TRANSIT_TO_BARRELS">
      <Motion_short_9x16_S2_FROM_TRANSIT_TO_BARRELS {...props} />
    </Sequence>
    <Sequence from={606} durationInFrames={390} name="S3_THE_FORECAST_ON_RECORD">
      <Motion_short_9x16_S3_THE_FORECAST_ON_RECORD {...props} />
    </Sequence>
    <Sequence from={996} durationInFrames={360} name="S4_BEYOND_THE_BARREL">
      <Motion_short_9x16_S4_BEYOND_THE_BARREL {...props} />
    </Sequence>
    <Sequence from={1356} durationInFrames={360} name="S5_THE_REBALANCE_TEST">
      <Motion_short_9x16_S5_THE_REBALANCE_TEST {...props} />
    </Sequence>
  </AbsoluteFill>
);

export const MidformVideo: React.FC<VariantProps> = (props) => (
  <AbsoluteFill style={{backgroundColor: '#081018'}}>
    <Sequence from={0} durationInFrames={630} name="S1_CHOKEPOINT_IN_VIEW">
      <Motion_midform_16x9_S1_CHOKEPOINT_IN_VIEW {...props} />
    </Sequence>
    <Sequence from={630} durationInFrames={735} name="S2_FROM_TRANSIT_TO_BARRELS">
      <Motion_midform_16x9_S2_FROM_TRANSIT_TO_BARRELS {...props} />
    </Sequence>
    <Sequence from={1365} durationInFrames={810} name="S3_THE_FORECAST_ON_RECORD">
      <Motion_midform_16x9_S3_THE_FORECAST_ON_RECORD {...props} />
    </Sequence>
    <Sequence from={2175} durationInFrames={735} name="S4_BEYOND_THE_BARREL">
      <Motion_midform_16x9_S4_BEYOND_THE_BARREL {...props} />
    </Sequence>
    <Sequence from={2910} durationInFrames={750} name="S5_THE_REBALANCE_TEST">
      <Motion_midform_16x9_S5_THE_REBALANCE_TEST {...props} />
    </Sequence>
  </AbsoluteFill>
);

export const shortDurationFrames = 1716;
export const midformDurationFrames = 3660;
export const authoredSegments: Array<{id: string; component: React.FC<VariantProps>; durationInFrames: number; width: number; height: number}> = [
  {id: 'Seg-short-9x16-S1-CHOKEPOINT-IN-VIEW', component: Motion_short_9x16_S1_CHOKEPOINT_IN_VIEW, durationInFrames: 282, width: 1080, height: 1920},
  {id: 'Seg-short-9x16-S2-FROM-TRANSIT-TO-BARRELS', component: Motion_short_9x16_S2_FROM_TRANSIT_TO_BARRELS, durationInFrames: 324, width: 1080, height: 1920},
  {id: 'Seg-short-9x16-S3-THE-FORECAST-ON-RECORD', component: Motion_short_9x16_S3_THE_FORECAST_ON_RECORD, durationInFrames: 390, width: 1080, height: 1920},
  {id: 'Seg-short-9x16-S4-BEYOND-THE-BARREL', component: Motion_short_9x16_S4_BEYOND_THE_BARREL, durationInFrames: 360, width: 1080, height: 1920},
  {id: 'Seg-short-9x16-S5-THE-REBALANCE-TEST', component: Motion_short_9x16_S5_THE_REBALANCE_TEST, durationInFrames: 360, width: 1080, height: 1920},
  {id: 'Seg-midform-16x9-S1-CHOKEPOINT-IN-VIEW', component: Motion_midform_16x9_S1_CHOKEPOINT_IN_VIEW, durationInFrames: 630, width: 1920, height: 1080},
  {id: 'Seg-midform-16x9-S2-FROM-TRANSIT-TO-BARRELS', component: Motion_midform_16x9_S2_FROM_TRANSIT_TO_BARRELS, durationInFrames: 735, width: 1920, height: 1080},
  {id: 'Seg-midform-16x9-S3-THE-FORECAST-ON-RECORD', component: Motion_midform_16x9_S3_THE_FORECAST_ON_RECORD, durationInFrames: 810, width: 1920, height: 1080},
  {id: 'Seg-midform-16x9-S4-BEYOND-THE-BARREL', component: Motion_midform_16x9_S4_BEYOND_THE_BARREL, durationInFrames: 735, width: 1920, height: 1080},
  {id: 'Seg-midform-16x9-S5-THE-REBALANCE-TEST', component: Motion_midform_16x9_S5_THE_REBALANCE_TEST, durationInFrames: 750, width: 1920, height: 1080},
];
