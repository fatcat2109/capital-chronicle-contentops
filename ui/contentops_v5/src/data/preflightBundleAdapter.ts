import { preflightBundlePacket } from './preflightBundlePacket';

export const preflightAdapter = {
  getPacket: () => preflightBundlePacket,
  getPlatformStates: () => preflightBundlePacket.platform_states,
  getRoomBindings: () => preflightBundlePacket.room_binding_prechecks,
  getSourceRefs: () => preflightBundlePacket.source_refs,
  getSafetyFlags: () => preflightBundlePacket.safety_flags,
  getCandidateFields: () => preflightBundlePacket.v5_candidate_fields,
};
