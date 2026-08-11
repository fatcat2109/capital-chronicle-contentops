import React from 'react';
import {Frame} from './scaffold';
import {
  Callout,
  ChapterCard,
  ChartScene,
  ComparisonScene,
  DisclaimerEndcard,
  DocumentScene,
  NumberCallout,
  SourceCard,
  TimelineScene,
  TitleOpening,
} from './primitives';
import type {SceneJob} from '../program/types';

/**
 * Exhaustive visual-primitive dispatcher. Each primitive is a genuinely
 * different layout; unsupported primitives fail closed rather than silently
 * falling back to a generic card.
 */
export const SceneRenderer: React.FC<{job: SceneJob} & Partial<SceneJob>> = (props) => {
  const job = (props.job ?? (props as unknown as SceneJob)) as SceneJob;
  let body: React.ReactNode;
  switch (job.visual_primitive) {
    case 'TITLE_OPENING':
      body = <TitleOpening job={job} />;
      break;
    case 'CHAPTER_CARD':
      body = <ChapterCard job={job} />;
      break;
    case 'CHART_SCENE':
      body = <ChartScene job={job} />;
      break;
    case 'DOCUMENT_SCENE':
      body = <DocumentScene job={job} />;
      break;
    case 'COMPARISON_SCENE':
      body = <ComparisonScene job={job} />;
      break;
    case 'TIMELINE_SCENE':
      body = <TimelineScene job={job} />;
      break;
    case 'NUMBER_CALLOUT':
      body = <NumberCallout job={job} />;
      break;
    case 'SOURCE_CARD':
      body = <SourceCard job={job} />;
      break;
    case 'CALLOUT':
      body = <Callout job={job} />;
      break;
    case 'DISCLAIMER_ENDCARD':
      body = <DisclaimerEndcard job={job} />;
      break;
    default: {
      const _exhaustive: never = job.visual_primitive;
      throw new Error(`unsupported_visual_primitive:${String(_exhaustive)}`);
    }
  }
  return <Frame job={job}>{body}</Frame>;
};
