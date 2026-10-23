# Lab03 H1 - AI extension review - Truong Thanh Dat

Issue: [#18](https://github.com/Computational-Thinking-Project/assistant_core_lab/issues/18).

## Request and feature

The user requested completion of Lab03 homework up to, but excluding, opening
pull requests. Codex selected the lab's suggested `help` feature: list the
assistant's existing greeting, tuition, office and handbook capabilities.
Implementation scope: `Message -> route -> AssistantService -> Response`.
No dependencies, API keys, network requests or user-history storage added.

## First generated implementation

Codex added `Intent.HELP`, exact command matching in the public router, a
deterministic service response, and routing/service/CLI tests. The first test
mutated the resolved responder's `explain` method. The existing service's
fallback router did not yet recognise help. The initial checks did not
explicitly cover serialized responses or raw-message logging.

## Three actual improvements performed by Codex

| # | Initial code / gap | Actual change | Reason and evidence |
|---|---|---|---|
| 1 | Public router supported help; `_default_route` did not. | Added equivalent help matching to the existing fallback router. | Consistent behaviour on both routes; regression test compares help, tuition and office cases. |
| 2 | Test modified a production responder instance after construction. | Injected a `NeverResponder` that fails if called. | The test directly proves that help does not need a provider, through the service's dependency-injection interface. |
| 3 | No explicit serialized-contract/privacy assertion. | Added a JSON-mode Response assertion and captured metadata logs. | Checks `intent=help`, empty sources, `degraded=False` and absence of the raw request from logs. |

These are **agent improvements**, not a claim that Dat manually reviewed or
authored them. They are evidence for Dat's review, not a substitute for it.

## Dat's required manual review before submission

- [ ] Read the changes in models, router, service and `tests/test_help.py`.
- [ ] Run `python -m assistant_core help` and `python -m assistant_core "?"`.
- [ ] Check that `help me with tuition` remains a fee request and that office
  questions mentioning `it helpdesk` still route to the office handler.
- [ ] Read each of the three improvements above; explain why it matters.
- [ ] Make and record any improvements you personally identify. Do not claim
  agent edits as personal edits. H1 asks for at least three improvements made
  by the student; the agent's three entries alone do not establish that.

| Personal observation | Change Dat actually made | Test / reason |
|---|---|---|
| To be completed after reading | | |
| To be completed after reading | | |
| To be completed after reading | | |

## Verification

Run from the repository root after installing the pinned requirements and
`pip install -e .`:

```sh
python -m pytest -q
python -m ruff check .
python -m assistant_core help
```

AI assistance is recorded in `docs/ai-use-log.md`. Dat opens the PR and
requests the agreed human reviewer; no approval or merged status is claimed.
