import React from 'react';
import {Composition} from 'remotion';
import {RetentionNativeBeat} from './beat';
import type {BeatRenderJob} from './types';

const defaultJob: BeatRenderJob = {
  video_id: 'preview', beat_id: 'preview-beat', scene_id: 'preview-scene', chapter_id: 'preview-chapter',
  variant_id: 'short_9x16', narrative_role: 'hook', viewer_takeaway: 'Evidence changes the story.',
  visual_purpose: 'Preview', narration_text: 'Evidence changes the story.', source_label: 'Capital Chronicle',
  duration_in_frames: 150, fps: 30, width: 1080, height: 1920, cache_key: 'preview', output_path: '',
  captions_visible: true,
  caption_safe_zone: {top: 0.08, right: 0.07, bottom: 0.16, left: 0.07},
  caption_layout: {left: 0.07, right: 0.07, bottom: 0.165, estimated_max_height_px: 154},
  proxy: false, caption_cues: [], edit_states: [],
};

export const RetentionNativeRoot: React.FC = () => (
  <Composition
    id="RetentionNativeBeat"
    component={RetentionNativeBeat}
    durationInFrames={defaultJob.duration_in_frames}
    fps={defaultJob.fps}
    width={defaultJob.width}
    height={defaultJob.height}
    defaultProps={{job: defaultJob}}
  />
);
