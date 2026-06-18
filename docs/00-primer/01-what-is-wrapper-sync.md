# What is wrapper-sync? (start here)

> **You don't need to know anything yet.** No Python, no git, no GitHub Actions. This page just
> tells you the *story*: what problem we had, and the one-button fix we built for it.

---

## The problem, in plain English

CleverTap makes a **native SDK** — the "real" library that apps use to talk to CleverTap. There's
one for Android (written in Kotlin/Java) and one for iOS (written in Objective-C/Swift). These get
new releases on their own schedule: bug fixes, new features, new public methods.

But lots of apps aren't written in pure Android or iOS. They're written in **cross-platform**
toolkits — Cordova, Flutter, React Native — where you write the app once (in JavaScript or Dart)
and it runs on both phones. For those apps to use CleverTap, we ship a **wrapper SDK**: a thin
layer that lets JavaScript/Dart code reach down and call the native Android/iOS methods.

> ### 🟦 Beginner sidebar: native SDK vs. wrapper SDK
> A **native SDK** is the real library for one platform. A **wrapper SDK** is the bridge that lets
> a cross-platform app *call into* that native library. CleverTap has wrappers for `clevertap-cordova`,
> `clevertap-flutter`, and `clevertap-react-native`. See [Glossary → Wrapper SDK](../GLOSSARY.md).

Here's the catch: **every time the native SDK releases, the wrappers have to catch up.** Someone
has to:

- bump the version number the wrapper points at (the "pin"),
- expose any new public methods through the bridge (JavaScript + Android + iOS),
- carry over any build changes (a new permission, a higher minimum Android version),
- update the changelog and the example apps,
- build everything to make sure it still compiles.

Doing all of that by hand, for three wrappers, every release, is **tedious and easy to get
wrong.** A method gets missed. A version gets bumped in four places but not the fifth. It's exactly
the kind of careful, repetitive work that humans are bad at and robots are good at.

> 🧠 **Analogy:** the native SDK is a **dictionary** that just added new words. Each wrapper is a
> **translation** of that dictionary into another language. When the dictionary grows, every
> translation has to be updated to match — or it falls out of date.

---

## The one-button promise

**wrapper-sync** is the automation that does that catch-up for you. The promise is simple:

> When a new native SDK is out, a maintainer clicks **one button**, picks the versions to sync to,
> and walks away. A few minutes later, a **pull request** appears — the wrapper code already updated
> to match the new native SDK — ready for a human to review and merge.

That's it. No editing five files by hand. No remembering the exact changelog format. The robot
reads what changed, makes the edits, builds the app to check its own work, and writes up a tidy
summary of everything it did.

> ### 🟦 Beginner sidebar: pull request (PR)
> A **pull request** is a proposal to merge a set of code changes. It shows the exact diff and gives
> people a place to review and comment before anything is merged. The output of wrapper-sync is
> *always* a PR — never a silent change. See [Glossary → Pull request](../GLOSSARY.md).

---

## Who clicks the button, and what do they get?

**Who:** a CleverTap **maintainer** — the person responsible for keeping a wrapper in step with the
native SDK. They click after a native release lands.

**Why a human clicks (instead of fully automatic):** native releases sometimes ship Android-only or
iOS-only. The maintainer is in the best position to say "both are out now — sync." One button
handles "Android only," "iOS only," or "both" without any guessing.

**What they get back:** a pull request that contains —

- the version pins bumped everywhere they live,
- new native methods surfaced through the bridge (where it was safe to do so),
- a structured summary of what was **surfaced / skipped / deferred / flagged for review**,
- the build result, and
- a cost report for the AI run.

The maintainer's only real job is to **read the PR and merge it.** The human is never removed from
the loop — the robot does the tedious 90%, the human approves.

> 🧠 **Analogy:** wrapper-sync is a **dishwasher**, not a maid. You still load it and you still put
> the dishes away (review + merge). But you're not scrubbing each plate by hand.

---

## The mental model you'll learn next

Everything in this system is a **4-layer onion**: a button (Trigger) calls a workflow (Conductor),
which hands a written prompt to an AI (Brain), which leans on a plain, no-AI fact tool (Ground
truth). A click travels *down* the layers; a finished PR travels back *up*.

You don't have to absorb that yet — the next page is entirely about it. Just hold onto the one-button
promise: **release happens → click → PR appears → human reviews.**

---

## ✅ Check yourself

<details>
<summary>1. Why do the wrapper SDKs need a "sync" at all?</summary>

Because the **native** Android/iOS SDKs release on their own schedule. When they add new methods,
bump versions, or change build settings, each wrapper has to catch up so cross-platform apps can use
the new capabilities. Keeping them in step by hand is tedious and error-prone.
</details>

<details>
<summary>2. Why is there a human clicking a button instead of fully automatic syncing?</summary>

Native releases are sometimes Android-only or iOS-only. The maintainer is best placed to decide
*when* to sync and *what* to sync, and one manual click cleanly handles "Android only," "iOS only,"
or "both."
</details>

<details>
<summary>3. What does the maintainer get back, and what's their job?</summary>

They get a **pull request** with the wrapper already updated (version pins, new APIs, a structured
summary, build result, cost). Their job is to **review and merge** it — the human approval is never
automated away.
</details>

**Next:** [02 — the 4-layer onion (the one model that explains everything) →](./02-the-4-layer-onion.md)
