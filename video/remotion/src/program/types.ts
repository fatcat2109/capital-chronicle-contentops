/**
 * Renderer-target render-job types. These are derived compiler output (a
 * replaceable target), never the canonical VideoProgram authority.
 */
export type VisualPrimitive =
  | 'TITLE_OPENING'
  | 'CHAPTER_CARD'
  | 'CHART_SCENE'
  | 'DOCUMENT_SCENE'
  | 'COMPARISON_SCENE'
  | 'TIMELINE_SCENE'
  | 'NUMBER_CALLOUT'
  | 'SOURCE_CARD'
  | 'CALLOUT'
  | 'DISCLAIMER_ENDCARD';

export type Aspect = 'landscape' | 'vertical';

export interface CaptionCue {
  start_frame: number;
  end_frame: number;
  text: string;
}

export interface NumberItem {
  label: string;
  value: number | string;
  unit?: string;
  delta?: string;
  emphasis?: boolean;
}

export interface SeriesDef {
  label: string;
  color?: string;
  points: {x: string; y: number}[];
}

export interface TextBlock {
  heading?: string;
  body?: string;
}

export interface AssetRef {
  kind: 'image' | 'chart' | 'map' | 'document';
  /** Absolute staticFile() key (assets/<sha256>.ext) resolved by the compiler. */
  path: string;
  sha256: string;
  layout?: 'focus' | 'side' | 'contain';
  caption?: string;
}

export interface SceneJob {
  scene_id: string;
  chapter_id: string;
  visual_primitive: VisualPrimitive;
  aspect: Aspect;
  width: number;
  height: number;
  fps: number;
  duration_in_frames: number;
  /** Duration of narration occupying this scene in seconds (visual tail excluded). */
  narration_seconds: number;
  display_title: string;
  subtitle?: string;
  kicker?: string;
  chapter_label?: string;
  source_label: string;
  credit_line?: string;
  disclosure?: string;
  numbers?: NumberItem[];
  series?: SeriesDef[];
  text_blocks?: TextBlock[];
  asset?: AssetRef | null;
  captions: CaptionCue[];
  rights_synthetic: boolean;
  motion_hint?: string;
  /** staticFile() key for the scene narration audio (relative to public/). */
  narration_asset?: string | null;
  /** Frames of silent tail reserved for the outgoing transition. */
  transition_tail_frames?: number;
}

export interface RenderJobBatch {
  batch_id: string;
  motion_system_version: string;
  renderer_profile: string;
  scenes: SceneJob[];
}

export interface ReceiptRow {
  scene_id: string;
  composition_id: string;
  output_path: string;
  duration_in_frames: number;
  width: number;
  height: number;
  fps: number;
  status: 'rendered' | 'failed';
  error?: string;
}
