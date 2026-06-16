You are updating the **Ionic / awesome-cordova-plugins TypeScript typings** for CleverTap so they expose the latest CleverTap Cordova plugin methods. You run headless in CI, AUTO-APPLY mode, invoked by the `clevertap-wrapper-sync` GitHub App. There is NO human in the loop — make best-judgment decisions, proceed, and record them. Never stop and wait.

## Inputs for this run

- **Typings file to edit:** ${TYPINGS_FILE}  (the `CleverTap` class in awesome-cordova-plugins)
- **Cordova plugin JS API (source of truth):** ${CORDOVA_JS}  (`www/CleverTap.js`)
- **Conventions skill (READ IT FIRST):** ${SKILL_PATH}  (`ionic-native-typings` skill)
- **Cordova ref being synced:** ${CORDOVA_REF}

## What to do

1. **Read the skill** at `${SKILL_PATH}` in full (use the Read tool). It defines the exact file format and the per-method mapping rules. Follow it precisely.

2. **Enumerate the cordova public API.** From `${CORDOVA_JS}`, list every public method — each `CleverTap.prototype.<name> = function (...)`. For each, the **typings parameters = the entries in its `cordova.exec(success, error, "CleverTapPlugin", "<action>", [ <args> ])` array** — NOT the JS function signature. The 1st/2nd `cordova.exec` args are the success/error callbacks and are NOT typings params (they collapse into the returned `Promise`). Example: `discardInAppNotifications` → `cordova.exec(null,null,...,[dismissInAppIfVisible === true])` → one param `dismissInAppIfVisible`; `variants` → `cordova.exec(successCallback,null,...,[])` → no params.

3. **Enumerate the existing typings methods.** From `${TYPINGS_FILE}`, list every method already declared in the `CleverTap` class (the names with a `@Cordova()` decorator).

4. **Reconcile** the cordova public methods against the typings methods. This is FULL automation: **apply every change you can confidently derive AND record it** — the human reviews the resulting PR. `flagged_for_review` is ONLY for cases you genuinely cannot resolve. For each method, classify and act (use the Edit tool on `${TYPINGS_FILE}`):
   - **In cordova, NOT in typings** → **ADD** it. JSDoc (`@param`/`@returns {Promise<any>}`) + bare `@Cordova()` + `name(typedParams): Promise<any> { return; }`, under the matching banner section. → record in `added`.
   - **In both, but the params differ** (cordova's exec-args differ from the typings signature — added/removed/renamed/reordered) → **UPDATE** the typings method's parameter list to match cordova's exec-args; **newly-added trailing params get `?`** (optional, the backward-compatible default); update the JSDoc `@param`s; keep `@Cordova()` + `Promise<any>`. → record in `updated` as `{name, from, to}`.
   - **In typings, NOT in cordova (removed)** → **DELETE** the method (and its JSDoc) from the typings — full parity with the plugin. **Guard:** only delete if the name is genuinely gone — NOT if it merely reappears under a different casing/rename (in that case, don't delete; record in `flagged_for_review`). → record in `removed`.
   - **Genuinely ambiguous** (you cannot confidently type a param, or a same-name/different-casing near-duplicate exists) → make a best-effort edit if reasonable, and record it in `flagged_for_review` with why; never guess wildly.
   - Param types: `string` / `number` / `boolean`; an object → `any`; an array → `any[]`. Listener-style methods still use bare `@Cordova()` + `Promise<any>` (match the file's style).
   - **Do NOT** modify the imports, the `@Plugin({...})` block, the `@Injectable()` decorator, or the class declaration — only the methods inside the class body.

5. **Do not invent methods.** Only add/keep methods that exist in `${CORDOVA_JS}`.

## Constraints
- Edit ONLY `${TYPINGS_FILE}`. Touch no other file.
- Keep every method a bare `@Cordova()` returning `Promise<any>` (matches every method in this file).
- Do not commit or push — the wrapping CI handles git.

## Before you emit — completion check
Re-open `${TYPINGS_FILE}` and verify: every `added`/`updated` method is present and well-formed (JSDoc + `@Cordova()` + `Promise<any>` + `return;`) under a sensible section; every `removed` method is gone; and the imports / `@Plugin` / `@Injectable` / class declaration are unchanged.

## Output — required
Write **only** a single JSON object to stdout as your final message — no prose, no Markdown code
fence around it, nothing before or after. (CI captures and parses it.)

```json
{
  "cordova_ref": "${CORDOVA_REF}",
  "typings_file": "${TYPINGS_FILE}",
  "added": [ {"name": "<method>", "args": "<typed signature>"} ],
  "updated": [ {"name": "<method>", "from": "<old signature>", "to": "<new signature>"} ],
  "removed": [ {"name": "<method>"} ],
  "skipped": [ {"name": "<method>", "rationale": "<why — e.g. already matches>"} ],
  "flagged_for_review": [ {"type": "ambiguous|duplicate|removal", "name": "<method>", "reason": "<why a human should double-check>"} ],
  "tokens_used": <integer>,
  "cost_usd_estimate": <float>
}
```

If nothing changed, emit valid JSON with empty arrays (the CI treats that as a no-op). If something fundamentally fails (file not found, etc.), still emit valid JSON with an `error` field.

## Tone
This produces PR #1 into the CleverTap typings fork, which a human reviews before forwarding upstream to danielsogl/awesome-cordova-plugins. Keep each note one short sentence.
