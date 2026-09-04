# AGENTS.md

## Project instruction

Project name: `codex_on_MQTT_project`

This file gives Codex project-level guidance.  
Before analyzing, editing, or generating code, read and follow this file.

## Working-directory alignment

This repository is the active MQTT project:

```text
C:\Users\paull_0duwwil\Dropbox\0DownLoad\codex_on_MQTT_project
```

For every MQTT-project shell command:

1. Begin the command with `Set-Location -LiteralPath 'C:\Users\paull_0duwwil\Dropbox\0DownLoad\codex_on_MQTT_project'` because the desktop shell may ignore its requested `workdir`.
2. Also set the command `workdir` to the same MQTT-project path when the tool supports it.
3. Verify the working directory with `Get-Location` when starting or resuming work.
4. Keep source-code paths relative to the repository after the shell is aligned.
5. Do not read, edit, generate, or test files in other project folders unless the user explicitly requests it.
6. If the Codex task's inherited default `pwd` points elsewhere, treat it as untrusted and realign each command explicitly.

## Firmware compilation safety

**ALERT: STOP DROPBOX SYNC before running the TI CCS compiler.**

When generating or compiling firmware, pause Dropbox synchronization before starting the TI Code Composer Studio (CCS) build. Resume synchronization only after the build has completed and its output files are no longer being written.

## Title Naming rule

if the titie as eg 'title_example V07 2026.06.24 17:32'
the version number should be added by one as 'V08'
the date should be changed as the today eg '2026.mm.dd hh:mm'    

## Auto QA progress record rule

Use `docs/qa_mqtt_progress_daily_digest.html` as the project's Question -> Answer progress record.

Write all future QA record summaries and details in Traditional Chinese. Preserve existing English records as historical evidence.

After completing a meaningful investigation, implementation, test, or engineering decision:

1. Automatically add one concise QA entry without waiting for a separate user request.
2. Record the question, the verified answer, and the supporting detail or next verification step.
3. Assign a stable three-digit index. Start at `001` and increment by one; never renumber older entries.
4. Display each record timetag as `(NNN YYYY-MM-DD HH:mm)`, for example `(007 2026-07-16 14:53)`.
5. Keep records in latest-to-oldest display order so the highest index appears first.
6. Keep entry details collapsed by default for fast reading and reduced scrolling.
7. Update the QA HTML title/footer by incrementing `Vnn` and applying the current timetag according to the Title Naming rule.
8. Do not create duplicate records for the same completed action. Do not mark assumptions or unverified hardware behavior as Answer.

## User abbreviation rules

The user often uses short abbreviation commands. Interpret them as task modifiers.

| Abbrev | Meaning |
|---|---|
| `go` | Read `AGENTS.md` first, then perform the requested work using the current project rules and handoff flow. |
| `di` | Discuss only the above mentioned issues, then give the next step and a recommendation. Do not edit files or run implementation commands unless the user later says `go` or explicitly asks to modify files. |
| `autorun` | Implement and run the already-discussed solution automatically. Run suitable project code, verify it, and open the completed HTML in Google Chrome. Continue autonomously except when a physical man-in-loop action is required. |
| `xx` | Development/checking layout: use two equal half-screen windows, with Codex on the left for interactive commands and the current `codex_on_xxx_project` folder in Explorer on the right for file/status checking. Here `xxx` is derived from the active project folder named by `pwd`; for example, `codex_on_MQTT_project` opens that same folder. Set Explorer to Details view, sorted by Date modified newest first, with no overlap. |
| `tc` | Reply in Traditional Chinese. |
| `en` | Reply in English. |
| `dd` | Deep Dive, Give detailed explanation |
| `gg` | Generate Graphic, diagram, call tree, flow chart, or visual explanation when useful. |
| `nu` | NUmeric explain method in step by step present how the priciple explore|
| `ss` | Significant Summarize youtube, paper, source, screenshot, video, transcript, PDF, or provided text. |
| `ee` | Enhencement English, Improve the user's English sentence and provide a clearer version and english and chinese both  |
| `li` | Perform `go` first, then run the Local Index html flow: build/check required local work, open local index.html automatically, and show the full index title ending with `completed`. |
| `gi` | Global index URL, automatic run whole process: build py->html->push->repo project->world wide URL, auto open repo index.html for checking; after open, show the full repo index title ending with `completed`. |

## Interpretation examples

- `in tc`  
  -> Reply in Traditional Chinese.

- `gg`  
  -> Provide a call tree or flow diagram in picture form.

## Coding style preference

Prefer practical, minimal, easy-to-modify code.

When editing existing code:

1. Do not rewrite the whole project unless requested.
2. Preserve existing function names and data flow when possible.
3. Prefer small patches with clear insertion locations.
4. Explain why the change fixes the issue.
5. Avoid breaking existing behavior.
6. Add debug prints only when useful and removable.
7. Keep compatibility with Windows and Linux paths when possible.
8. Prefer relative paths over hard-coded absolute paths.
9. Use the same in PC folder name and in Github repo project name otherwise given WARN message 

## Project path style

Use cross-platform path handling.

Prefer:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parent
csv_path = ROOT / "debug_inference" / "file.csv"
```

Avoid:

```python
csv_path = "C:\\Users\\..."
csv_path = "/home/user/..."
```

unless the user explicitly asks for physical absolute paths.

## Debug / analysis style

When checking bugs, report in this order:

1. Most likely root cause.
2. Evidence in code or log.
3. Minimal fix.
4. Safer long-term fix if needed.
5. Test method.

## Planning / status style

For development planning, present the plan as numbered steps and include a checklist/status table for user review.

Preferred format:

1. Define the data owner and input/output boundary.
2. Implement the smallest working producer path.
3. Verify locally.
4. Verify from another device.
5. Commit/push/open URL only after checks pass.

Checklist example:

| Step | Status | Check method |
|---:|---|---|
| 1 | Pending/In progress/Done | Specific command, URL, or visual check |
| 2 | Pending/In progress/Done | Specific command, URL, or visual check |

When working on UART/data/dashboard architecture, always state which process owns UART and which parts only read HTTP/MQTT data.
 
## Response style

Unless the user asks otherwise:

- Be direct.
- Prefer engineering explanation.
- Use tables for mappings.
- Use call trees for flow.
- Use concise comments in code.
- If user writes `tc`, answer in Traditional Chinese.
- If user writes `dd`, provide deeper detail.
