export type CaptionCue = {
  start_frame: number;
  end_frame: number;
  lines: string[];
};

export type EditState = {
  decision_id: string;
  at_frame: number;
  operation: string;
  asset_id?: string | null;
  asset_class?: string | null;
  asset_path?: string | null;
  attribution?: string | null;
  primary_visual_change: boolean;
  narrative_purpose: string;
  parameters: Record<string, unknown>;
};

export type BeatRenderJob = {
  video_id: string;
  beat_id: string;
  scene_id: string;
  chapter_id: string;
  variant_id: string;
  narrative_role: string;
  viewer_takeaway: string;
  visual_purpose: string;
  narration_text: string;
  source_label: string;
  duration_in_frames: number;
  fps: number;
  width: number;
  height: number;
  cache_key: string;
  output_path: string;
  captions_visible: boolean;
  caption_safe_zone: {top: number; right: number; bottom: number; left: number};
  caption_layout: {left: number; right: number; bottom: number; estimated_max_height_px: number};
  proxy: boolean;
  caption_cues: CaptionCue[];
  edit_states: EditState[];
};
