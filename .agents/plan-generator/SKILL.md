---
name: plan-generator
description: Research requested changes and create concise, ordered implementation plan documents in the project plan directory.
---

# Skill: Default Plan Document Generator

---

# [ID] - [short-title]

Type: feat | fix | refactor | chore
Branch: [type]/[id]-[short-title]

## Goal

<!-- One sentence per deliverable. Use imperative verbs. Be specific. -->

* [What to build/change — one line]
* [Observable output or behavior — one line]
* [Any data/logging requirement — one line]

## Context

<!-- Why this exists. 2–4 bullets max. No prose paragraphs. -->

* [Prior state or dependency]
* [What changed or what triggered this work]
* [Any known constraint or edge case to be aware of]

## Approach

<!-- Exact instructions. Where to work, what to do, what to avoid. -->

* Work in: `[file or directory]`
* Entry point / primary change: `[function, class, or module]`
* [Step 1 — specific action]
* [Step 2 — specific action]
* Do NOT touch: `[file or concern out of scope]`

## Scope control

* Use the smallest implementation that satisfies the acceptance criteria.
* Treat acceptance criteria as a closed list; useful improvements are not
  automatically part of the task.
* Before adding unplanned stored data, files, dependencies, or substantial
  verification steps, explain the addition and discuss scope with the user.
  Existing authorization covers additions already specified in the plan.
* Resolve routine implementation choices within the agreed scope without
  requesting confirmation.

## Acceptance

<!-- How to verify it's done. Testable, binary conditions. -->

* [ ] [Condition 1]
* [ ] [Condition 2]
* [ ] [Logs / output / schema field exists and correct]

---

## Skill Instructions

The template above is a default plan template from which to generate a plan
document in the plan directory according to its conventions. The skill may be
instructed to use another template, passed in by the user, which should be given
priority.

Prompt the user to provide a list of tasks to be incorporated into the plan
document. Then, research each task given the current codebase, and determine the
steps needed for an implementation. Group each set of tasks into natural commit
groups to be tackled, and write them into a plan document.

Typically the plan documents will be in the project directory /plan, with
filenames ordered in a numeric sequence - follow that pattern.

Plan document descriptions should focus on brevity and avoid verbosity.

Define concrete implementation limits where expansion is likely: supported
inputs, stored fields, file/module boundaries, and permitted abstractions. Specify
validation checks and test cases as a finite list proportional to the task; avoid
broad phrases such as "preserve everything" or "validate all inputs". Do not add
extra persistence, audit metadata, reusable frameworks, or speculative test
matrices unless requested. Make the required verification runs explicit.

Include the Scope control section in generated plans. Adapt implementation limits
and validation/test requirements to the user's task rather than imposing a fixed
number of files, checks, or tests on every project.
