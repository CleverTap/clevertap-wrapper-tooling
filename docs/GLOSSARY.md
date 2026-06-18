# Glossary

Every jargon word in this system, defined for someone seeing it for the first time. When a
walkthrough uses a term, it links back here. Skim it once now; return whenever a word trips you.

> Tip: the terms are grouped by topic, but you can also just `Ctrl/Cmd+F` for a word.

---

## The domain (CleverTap SDKs)

**Native SDK** — The "real" CleverTap library written for one platform: `clevertap-android-sdk`
(Kotlin/Java) and `clevertap-ios-sdk` (Objective-C/Swift). Apps written *natively* for Android
or iOS use these directly.

**Wrapper SDK** — A thin library that lets apps written in a *cross-platform* language
(JavaScript for Cordova/React Native, Dart for Flutter) call the native SDK underneath. It
"wraps" the native code. CleverTap has several: `clevertap-cordova`, `clevertap-react-native`,
`clevertap-flutter`. This whole system keeps wrappers in step with the native SDKs.

**Bridge** — The cross-language glue inside a wrapper. When JavaScript calls `recordEvent`,
the bridge carries that call down to the native Android/iOS method that actually does it. See
[bridge-layers walkthrough](./20-walkthroughs/build-cordova-action.md) and the
[Cordova bridge picture](./10-diagrams/).

**API surface** — The set of public methods the SDK exposes for others to call (e.g.
`recordEvent`, `onUserLogin`). "Surfacing an API" = exposing a new native method through the wrapper.

**Module** — A piece of a native SDK. Android has `core`, `pushtemplates`, `hms`; iOS has
`core`, `pushtemplates`. Each is versioned and tagged separately.

**Native release / version pin** — The exact native SDK version a wrapper depends on (e.g. the
Cordova plugin pins `clevertap-android-sdk:8.2.0`). "Bumping the pin" = pointing the wrapper at
a newer native version. A "sync" exists to do this safely.

**libVersion** — A version number encoded as a plain integer inside bridge code, computed as
`major*10000 + minor*100 + patch`. Example: `5.2.3` → `50203`. It's how the native SDK learns
which wrapper version is calling it.

**SemVer (semantic versioning)** — The `MAJOR.MINOR.PATCH` numbering rule. `MAJOR` = breaking
change, `MINOR` = new features (backward-compatible), `PATCH` = fixes only.

---

## The triage vocabulary (what the AI decides per change)

**Surfaced** — A native API change the AI *implemented* in the wrapper (added/updated the bridge).

**Skipped** — A change the AI deliberately did **not** expose (e.g. an internal-only helper).

**Deferred** — A change the AI couldn't safely auto-apply; left for a human, with a reason.

**Flagged for review** — A specific kind of deferral: the AI couldn't *confirm* something (e.g.
a method named in the changelog it couldn't find in source), so it raises a flag instead of guessing.

**Source verification** — The rule that the AI must *find the exact method/selector in the real
native source code* before writing a call to it. Guessing = a broken build. Non-negotiable.

**Recall pass** — A second sweep where the AI cross-checks the native **changelog** against the
[diff tool's](./20-walkthroughs/diff-native-api/) output, to catch the ~20% of changes the
regex parser misses.

---

## Python (the diff tool is written in it)

**Python** — A programming language. Files end in `.py`. You run one with `python3 file.py`.
No compile step.

**Standard library / stdlib** — The batteries included with Python itself. This tool uses
**only** the stdlib, so there's nothing to install (`no pip install needed`).

**`pip`** — Python's package installer (like an app store for libraries). Not needed here.

**Regex (regular expression)** — A mini-language for describing text patterns, e.g. "a line
starting with `public`, then a word, then `(`". The diff tool uses regex to *find method
declarations in source files* without fully understanding the code. Powerful but imperfect —
hence the ~80% coverage caveat and the recall pass.

**AST (abstract syntax tree)** — The "proper" way to parse code (a full grammar). The diff tool
deliberately does **not** use one — regex is simpler and good enough. Knowing the word helps you
understand the "regex-based, not AST" design note.

**dataclass** — A Python shorthand for a small data-holding object. `@dataclass` auto-writes the
boilerplate. `Symbol` and `Surface` in the diff tool are dataclasses.

**`frozen=True`** — Makes a dataclass *immutable* (can't change after creation). Immutable objects
can be used as dictionary keys and put in sets — which is how the tool dedupes/compares symbols.

**`set`** — A Python collection of *unique* items with fast math: `A - B` (in A but not B),
`A & B` (in both). The diff is literally `new_names - old_names` (added) and `old_names -
new_names` (removed). See [page 05](./20-walkthroughs/diff-native-api/05-diffing.md).

**`dict` (dictionary)** — A lookup table mapping keys to values. A **tuple key** like
`("android","core")` lets the tool look things up by *platform + module together*.

**`tomllib`** — A stdlib module (Python ≥ 3.11) that reads `.toml` config files. Used to read
Android's `gradle/libs.versions.toml` (its list of dependency versions).

**`pathlib` / `Path`** — Stdlib way to build file paths with `/` like Lego (`Path.home() /
".cache"`), instead of gluing strings. Works on Mac/Linux/Windows.

**`subprocess`** — Stdlib way to run another command-line program (here: `git`) from Python.

**`urllib`** — Stdlib way to download from the internet (here: a `.tar.gz` of the SDK source).

**tarball (`.tar.gz`)** — A compressed archive (like a `.zip`). GitHub serves a repo at a tag as
one. The tool downloads and unpacks it.

---

## git & GitHub

**git** — A version-control tool: it records every change to the code as a snapshot, so you can
branch, compare, and revert.

**Repository (repo)** — One project's folder tracked by git (e.g. `clevertap-cordova`).

**Branch** — An independent line of changes. The sync creates a fresh branch like
`task/release_2026-06-16` so its edits don't touch `develop` until reviewed.

**`develop` / base branch** — The main integration branch the sync starts *from* and opens its
PR *against*.

**Commit** — One saved snapshot of changes, with a message.

**Pull request (PR)** — A proposal to merge one branch into another, with a diff and a place to
review/comment. The whole automation's *output* is a PR.

**Tag** — A name pinned to a specific commit, used for releases (e.g. `corev8.2.0`). The diff
tool fetches source *at a tag*.

**`gh`** — GitHub's command-line tool. Scripts use `gh pr create`, `gh label create`, etc.

---

## GitHub Actions (the automation runner)

**GitHub Actions** — GitHub's built-in automation. It runs your scripts on GitHub's servers when
something happens (a button click, a push, a schedule).

**Workflow** — A `.yml` file describing a sequence of automated steps. Lives in
`.github/workflows/`.

**YAML (`.yml`)** — A text format for configuration (indentation matters, like Python). Workflows
are written in it.

**`workflow_dispatch`** — A trigger that means "run when a human clicks the button" (a manual
dispatch), as opposed to running automatically on a push.

**`workflow_call` / reusable workflow** — A workflow that other workflows can *call*, like a
shared function. `sync.yml` is one; each wrapper repo's tiny workflow calls it.

**Composite action** — A reusable bundle of steps (like a function within Actions), kept under
`.github/actions/`. Examples here: `setup`, `claude-sync`, `open-pr`, `build/*`.

**Runner** — The virtual machine a workflow runs on (e.g. `macos-14`, needed because building
iOS requires a Mac).

**Job / step** — A workflow has jobs; a job has steps. A step runs a command or an action.

**`if:` / gating expression** — A condition on a step deciding whether it runs. The trickiest
logic in `sync.yml` lives in these (e.g. "open the PR only if a sync succeeded and nothing was
cancelled"). See [the sync.yml walkthrough](./20-walkthroughs/sync-yml.md).

**Secret** — An encrypted value stored in the repo settings (API keys, tokens) that workflows can
read but humans can't see. This system needs four (App ID, App private key, Anthropic key, Slack URL).

**GitHub App** — A bot identity (`clevertap-wrapper-sync`) that can be granted permissions and
**mint short-lived tokens** to act on a repo (push a branch, open a PR) without using a person's
account.

**Token** — A temporary password that proves the bot is allowed to do something. Minted at the
start of a run, expires when it ends.

**Artifact** — A file a workflow saves for you to download afterward (e.g. the built APK, or
Claude's output logs).

---

## Claude-in-CI (the brain)

**Claude / LLM** — The AI model that does the actual code-wrapping. "LLM" = large language model.

**Headless** — Running Claude with no human chatting — it's given one prompt and runs to
completion on its own. Invoked as `claude -p "…"`.

**Prompt** — The written instructions handed to Claude. The big ones live in
[`prompts/`](../prompts/). Read [the orchestrator-prompt walkthrough](./20-walkthroughs/orchestrator-prompt-cordova.md)
to learn to "read a prompt as a program."

**`.claude/skills/`** — Per-repo expert instructions Claude auto-discovers and follows (the *real*
conventions for that wrapper). The prompt is the task; the skills are the know-how.

**Allowlist (`--allowed-tools`)** — The exact set of tools Claude is permitted to use in a run (e.g.
read files, edit files, run specific commands). A security boundary — anything not listed is denied.

**`envsubst`** — A tiny command that fills `${PLACEHOLDER}` blanks in a text file with real values.
Used to inject the version numbers etc. into the prompt before handing it to Claude.

**stream-json** — An output format where Claude emits one JSON event per line as it works (each
tool call, each result). Scripts read the final `result` event to get cost/token totals.

**`jq`** — A command-line tool for slicing JSON. Used to pull the `result` event out of the stream.

**Soft cap** — A cost threshold (e.g. $3) that, if exceeded, posts an informational PR comment.
It does **not** stop the run — just visibility.

**Self-heal** — An (optional/retired) retry loop: if a build fails, ask Claude to fix the code and
try again, up to N times.

---

## Build tooling (so the example apps compile)

**gradle** — Android's build tool. **`minSdk` / `targetSdk` / `compileSdk`** — the Android version
floors/targets an app declares; bumping `minSdk` can be a breaking change for host apps.

**CocoaPods (`pod`) / podspec** — iOS's dependency manager and its manifest file. **`Podfile.lock`**
pins exact pod versions; it must be deleted/regenerated when a pin changes.

**`cordova platform add/rm`** — Cordova commands that regenerate the native project folders so new
plugin pins take effect. **google-services.json** — a Firebase config file the Android build needs;
CI writes a stub.
