import React from 'react';
import {Composition} from 'remotion';
import {AssetFirstTreasuryMidform, AssetFirstTreasuryShort, MIDFORM_FRAMES, SHORT_FRAMES} from './generated/assetFirstTreasury';

export type ProofProps = {proofId: string; creativeSourceSha256: string; captionsVisible: boolean};
const defaults: ProofProps = {proofId: 'ASSET_FIRST_TREASURY_CURVE', creativeSourceSha256: 'preview', captionsVisible: false};

export const Root: React.FC = () => <>
  <Composition id="AssetFirstTreasuryShort" component={AssetFirstTreasuryShort} durationInFrames={SHORT_FRAMES} fps={30} width={1080} height={1920} defaultProps={defaults}/>
  <Composition id="AssetFirstTreasuryMidform" component={AssetFirstTreasuryMidform} durationInFrames={MIDFORM_FRAMES} fps={30} width={1920} height={1080} defaultProps={defaults}/>
</>;
