# Repository instructions

## Implementation scope

- Prefer the smallest implementation that satisfies the agreed plan.
- Treat acceptance criteria and validation requirements as closed lists.
- Keep speculative format support, defensive checks, abstractions, audit
  metadata, duplicate representations, and test matrices outside the scope
  unless explicitly requested.
- Before adding unplanned stored data, files, dependencies, or substantial
  verification steps, explain why, explicitly prompt the user for a scope
  decision, and wait for their reply before implementing the addition.
  Existing authorization covers work already requested or specified in the plan.
- Resolve routine implementation choices within the agreed scope without
  requesting confirmation.
- Store each data field once in ordinary columns. Retain source files separately
  when original formatting matters.
- Run the verification specified by the plan. Repeat expensive checks only when
  a failure or unresolved concern justifies it.

## Readability

- Separate distinct phases with blank lines and very brief comments.
- Identify each input file's import section.
- Label preparation, import, transformation, validation, and output phases.
- In SQL, briefly identify intermediate results and each comparison.
- In fixtures, separate setup, execution, and assertions.
- Explain purpose or a non-obvious choice; avoid narrating every statement.

## Commits

- Use conventional commit subjects and concise bullet-point bodies.
- Keep every commit-message line within 80 characters.
- Fold follow-up changes into the appropriate implementation commit group when
  requested.
- Do not push unless explicitly instructed.
