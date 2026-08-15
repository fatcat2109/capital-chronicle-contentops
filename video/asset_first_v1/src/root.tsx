import React from 'react';
import {Composition} from 'remotion';
import {AssetFirstTreasuryMidform, AssetFirstTreasuryShort, MIDFORM_FRAMES, SHORT_FRAMES} from './generated/assetFirstTreasury';
import {PositioningProps, TreasuryPositioningLongform, TreasuryPositioningShort} from './generated/treasuryPositioning';

export type ProofProps = {proofId: string; creativeSourceSha256: string; captionsVisible: boolean};
const defaults: ProofProps = {proofId: 'ASSET_FIRST_TREASURY_CURVE', creativeSourceSha256: 'preview', captionsVisible: false};

export const Root: React.FC = () => <>
  <Composition id="AssetFirstTreasuryShort" component={AssetFirstTreasuryShort} durationInFrames={SHORT_FRAMES} fps={30} width={1080} height={1920} defaultProps={defaults}/>
  <Composition id="AssetFirstTreasuryMidform" component={AssetFirstTreasuryMidform} durationInFrames={MIDFORM_FRAMES} fps={30} width={1920} height={1080} defaultProps={defaults}/>
  <Composition id="TreasuryPositioningShort" component={TreasuryPositioningShort} durationInFrames={1500} fps={30} width={1080} height={1920} defaultProps={{...defaults,variant:'short',scenes:[],audioFile:'audio/short.wav',governedPositions:[]} as PositioningProps} calculateMetadata={({props})=>({durationInFrames:Math.max(1,Math.ceil(props.scenes.reduce((sum,row)=>sum+row.duration_seconds,0)*30))})}/>
  <Composition id="TreasuryPositioningLongform" component={TreasuryPositioningLongform} durationInFrames={13500} fps={30} width={1920} height={1080} defaultProps={{...defaults,variant:'longform',scenes:[],audioFile:'audio/longform.wav',governedPositions:[]} as PositioningProps} calculateMetadata={({props})=>({durationInFrames:Math.max(1,Math.ceil(props.scenes.reduce((sum,row)=>sum+row.duration_seconds,0)*30))})}/>
</>;
