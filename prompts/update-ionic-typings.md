You are updating the **Ionic / awesome-cordova-plugins TypeScript typings** for CleverTap so they expose the latest CleverTap Cordova plugin methods. You run headless in CI, AUTO-APPLY mode, invoked by the `clevertap-wrapper-sync` GitHub App. There is NO human in the loop — make best-judgment decisions, proceed, and record them. Never stop and wait.

## Inputs for this run

- **Typings file to edit:** ${TYPINGS_FILE}  (the `CleverTap` class in awesome-cordova-plugins)
- **Cordova plugin JS API (source of truth):** ${CORDOVA_JS}  (`www/CleverTap.js`)
- **Conventions skill (READ IT FIRST):** ${SKILL_PATH}  (`ionic-native-typings` skill)
- **Cordova ref being synced:** ${CORDOVA_REF}

## What to do

1. **Read the skill** at `${SKILL_PATH}` in full (use the Read tool). It defines the exact file format and the per-method mapping rules. Follow it precisely.

2. **Enumerate the cordova public API.** From `${CORDOVA_JS}`, list every public method — each `CleverTap.prototype.<name> = function (<args>)`. Capture the method name and its argument list. (Use the Grep/Read tools.)

3. **Enumerate the existing typings methods.** From `${TYPINGS_FILE}`, list every method already declared in the `CleverTap` class (the names with a `@Cordova()` decorator).

4. **Compute the missing set** = public cordova methods NOT already present in the typings (match by exact method name). These are the candidates to add.

5. **Add each missing public method** to `${TYPINGS_FILE}` (use the Edit tool), following the skill's per-method pattern exactly:
   - JSDoc (`@param`/`@returns {Promise<any>}`) + bare `@Cordova()` + `name(typedArgs): Promise<any> { return; }`.
   - **Drop the success-callback parameter** (it collapses into the returned Promise).
   - Type the remaining args: `string` / `number` / `boolean`; an object → `any`; an array → `any[]`.
   - Place each method under the **matching banner-comment section** (Events, User Profile, App Inbox, Display Units, Product Config, Variables, Custom Templates, …); create a new banner only for a genuinely new area.
   - Keep `@deprecated` notes for any method the cordova JS marks/comments as deprecated.
   - **Do NOT** modify the imports, the `@Plugin({...})` block, the `@Injectable()` decorator, or the class declaration — only add methods inside the class body.

6. **Do not invent methods.** Only add methods that actually exist in `${CORDOVA_JS}`. If a method's shape is ambiguous (e.g. an overload, or an argument you can't confidently type), add it best-effort and note it in `flagged`, or skip it and note it in `skipped` — never guess wildly.

## Constraints
- Edit ONLY `${TYPINGS_FILE}`. Touch no other file.
- Keep every method a bare `@Cordova()` returning `Promise<any>` (matches every method in this file).
- Do not commit or push — the wrapping CI handles git.

## Before you emit — completion check
Re-open `${TYPINGS_FILE}` and verify: every method in your `added` list is present, well-formed (JSDoc + `@Cordova()` + `Promise<any>` + `return;`), under a sensible section, and the `@Plugin`/imports are unchanged.

## Output — required
Write a single JSON object to stdout (CI captures it):

```json
{
  "cordova_ref": "${CORDOVA_REF}",
  "typings_file": "${TYPINGS_FILE}",
  "added": [ {"name": "<method>", "args": "<typed signature>"} ],
  "skipped": [ {"name": "<method>", "rationale": "<why — e.g. already present / internal>"} ],
  "flagged": [ {"name": "<method>", "rationale": "<why a human should double-check>"} ],
  "tokens_used": <integer>,
  "cost_usd_estimate": <float>
}
```

If nothing is missing, emit valid JSON with an empty `added` array (the CI treats that as a no-op). If something fundamentally fails (file not found, etc.), still emit valid JSON with an `error` field.

## Tone
This produces PR #1 into the CleverTap typings fork, which a human reviews before forwarding upstream to danielsogl/awesome-cordova-plugins. Keep each note one short sentence.
