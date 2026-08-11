export type Primitive =
  | 'COLD_OPEN'
  | 'CHAPTER_RUPTURE'
  | 'ILLUSTRATION_ATMOSPHERE'
  | 'CURVE_MORPH'
  | 'TIMELINE_TRACE'
  | 'SOURCE_EVIDENCE'
  | 'COMPARISON_FIELD'
  | 'KINETIC_STATEMENT'
  | 'BOUNDARY_CLOSE'
  | 'ENTITY_PORTRAIT'
  | 'MAP_FIELD';

export type CaptionCue = {start_frame: number; end_frame: number; text: string};
export type DataPoint = {label: string; value: number};
export type Series = {label: string; unit?: string; points: DataPoint[]; color?: string};

export type SceneJob = {
  scene_id: string;
  chapter_id: string;
  primitive: Primitive;
  aspect: 'landscape' | 'vertical';
  width: number;
  height: number;
  fps: number;
  duration_in_frames: number;
  title: string;
  deck?: string;
  kicker?: string;
  statement?: string;
  chapter_number?: string;
  source_label: string;
  rights_label?: string;
  disclosure?: string;
  numbers?: {label: string; value: string; note?: string}[];
  series?: Series[];
  asset_path?: string | null;
  asset_role?: string | null;
  captions: CaptionCue[];
  narration_asset: string;
  accent?: 'signal' | 'mint' | 'cobalt' | 'amber';
  transition?: string;
  title_scale?: number;
  caption_scale?: number;
  asset_scale?: number;
  show_legend?: boolean;
  source_compact?: boolean;
};
