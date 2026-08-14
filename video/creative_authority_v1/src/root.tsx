import React from 'react';
import {Composition} from 'remotion';
import {
  ArchitectureProofMidform,
  ArchitectureProofShort,
  MIDFORM_FRAMES,
  SHORT_FRAMES,
} from './generated/architectureProof';

export type ProofProps = {
  architectureProofId: string;
  creativeSourceSha256: string;
  captionsVisible: boolean;
};

const defaults: ProofProps = {
  architectureProofId: 'ARCHITECTURE_PROOF_ONLY',
  creativeSourceSha256: 'preview',
  captionsVisible: false,
};

export const Root: React.FC = () => (
  <>
    <Composition
      id="CreativeAuthorityShort"
      component={ArchitectureProofShort}
      durationInFrames={SHORT_FRAMES}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={defaults}
    />
    <Composition
      id="CreativeAuthorityMidform"
      component={ArchitectureProofMidform}
      durationInFrames={MIDFORM_FRAMES}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={defaults}
    />
  </>
);
