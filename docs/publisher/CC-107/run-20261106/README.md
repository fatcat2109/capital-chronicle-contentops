# CC-107: NFP preview and event article frame

The NFP preview is live at
https://capitalchronicle.substack.com/p/nfp-preview-why-a-payroll-beat-needs.
It published web-only at 12:58:16.717Z on 6 November, before the 13:30Z event.
The same operation delivered all eight social destinations and the additional
LinkedIn company identity. X and LinkedIn media readbacks are being completed;
YouTube retained the approved text but dropped its uploaded chart. Its exact
public object is retained with a content-incomplete result, without a repost.

The live published feed holds one EVENT_PREVIEW row. The installed Main digest
consumer includes its canonical URL, as proved by
[the live consumer readback](live-consumer-readback.json). This executes the
consumer without sending email or changing a schedule.

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

The implementation through 72ad0516 is pushed and integrated into the Publisher
operating root. The first KEEP remains 12:46:27.585514Z: canonical publication met
the 15-minute target, while completion of all social sends missed it.
The post-event NFP review and CPI preview acceptance still require their dated Main
inputs and actual article/digest-consumer readback. Midterm work remains separate.
No schedule, chat message or native desktop-control action was performed.
