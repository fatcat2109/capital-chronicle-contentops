# Media Manifest

## Owner master

- Local path: `.task-runtime/frozen_without_breaking/deliverables/Frozen_Without_Breaking_owner_polish_1080p_master.mp4`
- SHA-256: `C571D41470ACEC45317A1324698420F2C1B7537EB73090F8D3420327CF393227`
- Size: `387,542,692` bytes
- Duration: `848.366667s` (`14:08.367`)
- Frames: `25,451`
- Video: H.264, `1920×1080`, `30/1 fps`, `yuv420p`, limited/TV range, BT.709 primaries/transfer/matrix, `3,391,630 bps`
- Audio: AAC, `48,000 Hz`, stereo, `254,027 bps`
- Overall bitrate: `3,654,482 bps`
- Complete video+audio decode: exit `0`, `24.482s`
- Demuxed assembled-picture video SHA-256: `cd98763513d06f59cc7030c7203432e9056e7c5cfdfc5cac4b87704296bcfea7`
- Demuxed muxed-master video SHA-256: `cd98763513d06f59cc7030c7203432e9056e7c5cfdfc5cac4b87704296bcfea7`
- Audio-only mux proof: matching demuxed video hashes establish that the final AAC mux did not re-encode picture.
- Attachment derivative: not created; the owner master itself is below approximately 480 MB.

## Final normalized picture units

All are H.264 `1920×1080`, 30 fps, yuv420p limited BT.709 and live under `.task-runtime/frozen_without_breaking/production/renders/chapters_normalized_bt709/`.

| Unit | Status | SHA-256 |
|---|---|---|
| Chapter 1 | repaired/locked | `5A64996954E3C6CFAC142272479E533D516D151025418EA2E5FA2FC4C46F2C6C` |
| Chapter 2 | repaired/locked after same-author margin revision | `0D1C68C5FC660513FA21166AA7A4F7D37581EE8E8606CE5ED07EBF7EC1638434` |
| Chapter 3 | repaired/locked | `429AF2540D33E63A7EA7800A996136C1B15259D049A536DE5D72F1A0705B61AB` |
| Chapter 4 | repaired/locked | `3DEA2740D73D7CC831AD8710CEBE1E6EF73683F499AA531A96C25D5B6C5A7D24` |
| Chapter 5 | unchanged picture reused; old audio stripped | `3FA4311A4DEFAC2F31ED9B7E9063443CDA36438B193061FCA3CC1B04F8DA25C7` |
| Chapter 6 | repaired/locked | `935BBAEF42E0823760931040C61497C1446CE11C54F935592FC35AADA355991E` |
| Chapter 7 | repaired/locked | `F87B72F2E86D49921651819DC93B548E34082272D35249D0897DF69C547411C7` |

Assembled picture SHA-256: `9685471ef572aa324f55871502f65df7e351caf3b1d56590b30b765cdf069d96`.

## Audio

- Narrator engine: `kokoro-onnx 0.4.9`, local CPU
- Voice/settings: `af_heart`, speed `1.06`, language `en-us`
- Narration: all seven stems regenerated; no time-stretch or retime
- Final PCM mix: `.task-runtime/frozen_without_breaking/audio_build/final_mix_48k_stereo_zero_tail.wav`
- Final PCM SHA-256: `4C5DAC48D10AE8E9B1F5FCEE7C333425E7A9E1E1C3363DFDB42795CBD99394E7`
- Measured final PCM: `-15.97 LUFS-I`, `-1.49 dBTP`, `3.10 LU` LRA
- Final two seconds: digital zero, measured peak `0`, nonzero samples `0`
- Premaster: `-21.67 LUFS-I`, `-2.40 dBTP`
- Narration bus SHA-256: `c12aabb8d6290dddd680a199116c5b74b3cbb07694d60d79cad5e30f080d1791`
- Authority bus SHA-256: `3cc8e490dcf96805479087b0ebce4da04176f531a656070fdade2612ff92eec7`
- Music bus SHA-256: `097d1c76026046855878a63f4fcc3f77617e945edd137fd545ae4a530d13de08`
- Designed-sound bus SHA-256: `9ac667d1c7a598bf99898cbcfb32b97dd4370b7b0e0fe83e72b4ed18bc272416`
- Premaster SHA-256: `ac9f60de297481070d8a6c59bfae780959cc908cb32e9f8f86c4271ed30ae0f5`

Narration durations were `112.711`, `110.266`, `119.081`, `94.629`, `97.777`, `94.857`, and `146.145` seconds for Chapters 1–7 respectively.

## Review images

Six actual-master dense sheets were generated at one frame every four seconds, 36 frames per 1920×1080 sheet, under `.task-runtime/frozen_without_breaking/review/final_dense/`. Targeted authority and dirty-range contacts remain under `.task-runtime/frozen_without_breaking/review/`.
