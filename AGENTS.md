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

## Development environment

- Before starting a Docker Compose development environment, inspect the project's
  Compose configuration and existing service status with `docker compose ps`.
- Reuse running development services for implementation and verification. Do not
  start a second environment or recreate or restart containers unless a required
  change or an observed failure makes it necessary.

## Readability

- Separate distinct phases with blank lines and very brief comments.
- Keep imports grouped at the top of each input file.
- Make preparation, import, transformation, validation, and output phases clear
  through structure and brief, natural comments where useful. These are concepts,
  not literal comment phrases, headings, or prefixes such as "Preparation:" or
  "Transformation:". Omit labels that merely narrate the code.
- In SQL, briefly identify intermediate results and each comparison.
- In fixtures, separate setup, execution, and assertions.
- Explain purpose or a non-obvious choice; avoid narrating every statement.

## Frontend organization

- Group components by feature under `web/src/components/`.
- Keep page entry points focused on shared state, queries, and coordination.
- Name components after the data type or value they render, and name state and
  handlers after what they control. Avoid vague names.
- Keep component implementations in named files. Use directory index files
  to expose feature entry points; keep internal imports direct.
- Use Prettier for JS/JSX formatting and preserve unrelated user edits.
- Place details where they have enough space and remain reachable alongside
  existing scrolling and floating panels. Check the complete interaction on
  desktop and narrow screens.

## Validation reporting

- Describe planned tests briefly in plain English: what behavior they check
  and why it matters. Keep individual cases, fixture values, expected totals,
  and assertion mechanics in test code, not the plan.
- State required verification commands without translating tests into prose.
- Keep validation results to terse bullets stating the check and outcome.
- Include only required measurements and material limitations or failures.
- Do not repeat acceptance criteria, test mechanics, or execution history.

## Commits

- Use conventional commit subjects and concise bullet-point bodies.
- Keep every commit-message line within 80 characters.
- Fold follow-up changes into the appropriate implementation commit group when
  requested.
- Keep formatting-only changes in separate commits from behavior and refactors.
- Do not push unless explicitly instructed.
