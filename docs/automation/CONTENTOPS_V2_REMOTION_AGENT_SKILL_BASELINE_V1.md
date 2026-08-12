# ContentOps V2 — Remotion Agent Skill Baseline V1

Authority date: 2026-08-12
Status: `CURRENT_V2_REMOTION_TECHNICAL_REFERENCE_BASELINE`

Purpose: pin a reproducible Remotion technical-reference baseline for V2 creative-code work without importing a third-party creative style as Capital Chronicle product authority.

## 1. Primary technical authority — official Remotion Agent Skills

Repository:

`remotion-dev/skills`

Pinned commit inspected for this baseline:

`b12104ef5f1b1ca2ca5590fcc7c1804fbc85556f`

Snapshot observed 2026-08-12:

- maintained by the official `remotion-dev` organization;
- repository created 2026-01-19;
- pushed 2026-08-11;
- approximately 4.2k GitHub stars and approximately 490 forks at the time of inspection;
- current official skill metadata reports Remotion skill version `4.0.508`.

The star/fork counts are a discovery snapshot only and are not product authority.

### Mandatory official files for GPT-5.6 creative-code tasks

Read/pin from the official commit rather than relying on memory:

1. `skills/remotion-best-practices/SKILL.md`
   - router for current Remotion skills;
   - use it to choose the relevant specialist references.

2. `skills/remotion-markup/SKILL.md`
   - current React/Remotion markup guidance;
   - frame-driven `useCurrentFrame()` / `interpolate()` animation;
   - easing/spring support;
   - sequencing/assets/media/effects/maps/audio/captions/text measurement/render references.

3. Relevant `remotion-markup` references when the task touches them:
   - `timing.md`
   - `transitions.md`
   - `video-editing.md`
   - `sequencing.md`
   - `multi-scene-video.md`
   - `measuring-text.md`
   - `measuring-dom-nodes.md`
   - `images.md`
   - `effects.md`
   - `audio.md`
   - `sfx.md`
   - `voiceover.md`
   - `text-highlights.md`
   - `calculate-metadata.md`

4. Specialist official skills as required:
   - `skills/remotion-maps/SKILL.md`
   - `skills/remotion-captions/SKILL.md`
   - `skills/remotion-multimedia/SKILL.md`
   - `skills/remotion-render/SKILL.md`
   - `skills/remotion-docs/SKILL.md`
   - `skills/remotion-upgrade/SKILL.md`

### V2 interpretation

The official Remotion skill is technical craft/reference authority, not Capital Chronicle creative direction.

Keep these principles:

- animation must be deterministic/frame-driven for render reliability;
- use appropriate easing/springs rather than relying on browser CSS transitions;
- measure/fix text overflow instead of trusting approximate typography;
- use explicit sequencing/timing;
- use current asset/media/caption/audio APIs correctly;
- render and inspect actual output;
- use current official docs for API uncertainty.

Do not turn examples in the skill into a universal visual template. A fade example is an API example, not a mandate to fade every title.

## 2. Community reference — `haidrrrry/claude-remotion-skill`

Repository snapshot observed 2026-08-12:

- created 2026-06-13;
- roughly 40 GitHub stars;
- MIT license;
- contains `remotion-motion-graphics/SKILL.md` plus motion/design references.

Useful craft ideas to borrow selectively:

- generic AI-video quality is often caused by weak motion-design craft rather than React code syntax;
- avoid opacity-only entrances as a default;
- use multi-property choreography where appropriate;
- stagger elements when it serves hierarchy;
- exits can be faster than entrances;
- inspect rendered frames and iterate;
- test safe zones/overflow/layer ordering.

Do **not** adopt its absolute rules wholesale. In particular, V2 rejects these as universal rules:

- “stagger everything”;
- “every still image gets Ken Burns”;
- “idle elements breathe”;
- a mandatory five-layer visual stack for every scene.

Applied globally, those rules would create exactly the repetitive generated-motion signature Jim rejected. Capital Chronicle requires editorially motivated variation, including hard cuts and intentional stillness where stronger.

## 3. Community reference — `BayramAnnakov/remotion-video-director`

Repository snapshot observed 2026-08-12:

- created 2026-03-13;
- roughly 40 GitHub stars;
- `SKILL.md` version `2.0.0`;
- explicitly positions itself as a creative/strategic layer alongside the official Remotion skill.

Useful conceptual ideas:

- separate creative strategy (“what should this video be?”) from API mechanics (“how do I implement this in Remotion?”);
- define audience, purpose, emotional arc, audio strategy, scene/shot purpose, and review criteria before rendering;
- actual rendered review matters more than code inspection.

Do not copy its interactive user-question workflow into autonomous V2 runtime. Do not adopt its default cross-dissolve-every-scene or static archetype recipes as product rules. GPT-5.6 creative authorship must make shot-specific decisions from the governed story.

## 4. Community reference — `wshuyi/remotion-video-skill`

Repository snapshot observed 2026-08-12:

- created 2026-01-25;
- roughly 330 GitHub stars / roughly 58 forks;
- focused on programmatic Remotion video generation.

It is a useful popularity signal and implementation reference, but its older/simple scene-template orientation is not the V2 creative authority. Do not import it wholesale. V2 specifically rejects a return to one-scene/one-template grammar.

The repository does not advertise a license in the inspected GitHub metadata. Reference concepts only; do not vendor/copy code without a compatible license review.

## 5. Precedence

For V2 implementation:

```text
Jim current owner direction
→ ContentOps V2 North Star / GPT-5.6 owner override / task authority
→ current official Remotion docs + pinned remotion-dev/skills
→ committed ContentOps renderer/security contracts
→ selectively useful community craft references
```

Community popularity never overrides official API guidance or ContentOps product constraints.

## 6. How Codex should use these references

The next V2 task should not install random community skills into the repository or grant them autonomous authority.

Preferred workflow:

1. Fetch/read the pinned official `remotion-dev/skills` files required for the task.
2. If internet/current GitHub access is available, verify official `main` has not materially changed; if it has, record the new exact commit before using it.
3. Read the two selected community skill files only for motion-design heuristics/review prompts.
4. Extract a compact task-local design checklist.
5. Let exact `new/gpt-5.6-sol-xhigh` author the actual shot/edit/motion code for this story.
6. Validate generated code against ContentOps sandbox/import/path rules.
7. Render real media and inspect it; never promote a skill's checklist score to visual acceptance.

## 7. Capital Chronicle-specific anti-patterns

Regardless of any external skill, reject:

- repeated same-speed text transitions;
- repeated same-direction reveals;
- slow full-chart wipes when a fast focused delta/annotation is clearer;
- text collision/overflow;
- universal Ken Burns;
- universal micro-motion;
- excessive parallax for decoration;
- cross-dissolve between every scene;
- one animation component reused across most of a video;
- animation whose only purpose is to satisfy a “motion count” metric;
- assets used merely to increase count without editorial purpose.

The goal is authored editorial rhythm: hard cuts, rapid reveals, pauses, reframes, document punches, chart annotations, photo/B-roll changes, map motion, and silence/hold moments should vary according to narrative meaning.
