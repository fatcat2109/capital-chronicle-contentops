# CC-107: NFP preview and event article frame

The event briefs are wired into the existing native writer. The private NFP preview
is qualified with eight compiled derivative previews, using CC-216's reviewed
background, the held current Investing.com consensus fact and exact excerpts of
Main's dossier frozen at 10:03:37Z on 6 November. This preview has not yet been
published. The same writer's one editor check resumes after a quota interruption.

The [readable draft](article-draft.md) and [actual writer validation](writer-validation.json)
retain the content and source checks. The [runtime consumer readback](runtime-writer-consumer.json)
proves the actual writer received the event frame and frozen dossier. The
[quota continuation](quota-continuation.json) records the interruption without
inventing approval or publication.

285 targeted tests passed before the 18:30 GMT+7 blackout. Later source-context and
source-span fixes were checked through the real product validators and pipeline;
new regression cases are authored but unrun during the blackout. No whole-suite,
parallel or blackout pytest run was started. Existing unrelated JSONL changes
remain outside these commits.

The latest pushed and integrated implementation is e65deaa351170532bb1cfed4f5b1c9bb3219872e.
The post-event NFP review and CPI preview acceptance still require their dated Main
inputs and actual article/digest-consumer readback. Midterm work remains separate.
No schedule, chat message or native desktop-control action was performed.
