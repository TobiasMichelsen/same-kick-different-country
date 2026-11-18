# Claude annotations

Everything the model annotates, plus exactly what it was asked, so the run can be
reported and repeated.

| File | Contents |
|---|---|
| `prompt_zeroshot.md` | The exact zero-shot prompt: instructions, coding guide version, model id and date (no examples) |
| `claude_zeroshot.csv` | The 10 shared posts coded with the zero-shot prompt |
| `prompt.md` | The exact few-shot prompt: instructions, coding guide version, the 15 human-coded examples, model id and date |
| `claude.csv` | The 10 shared posts coded with the few-shot prompt (agreement check) + the 25 posts assigned to `claude` in `../sample_posts.csv` |

The sheets use the same columns as `../sheets/annotator_N.csv`, so the agreement
script can read human and model sheets the same way. Units Claude was unsure about
are explained in the `notes` column.

## Procedure (decided 2026-11-17)


1. **Human sheets and zero-shot run.** The three annotators code their 25 posts each:
   the 10 shared posts and 5 posts each codes alone. Meanwhile Claude codes the 10
   shared posts with the coding guide only, no examples (`claude_zeroshot.csv`). This
   run uses no human labels, so it can happen before the sheets are finished.
2. **Few-shot prompt.** The prompt is the coding guide plus examples taken **only**
   from the posts coded by a single annotator (5 from each annotator, 15 in total).
   Human labels for the 10 shared posts never go into the prompt.
3. **Agreement check.** In a fresh session, Claude codes the 10 shared posts with the
   few-shot prompt. 
4. **Decision.** If the few-shot agreement holds up, Claude codes the 25 `claude`
   posts and the extra posts with the same prompt. If not, the guide is tightened and
   step 3 is repeated.
