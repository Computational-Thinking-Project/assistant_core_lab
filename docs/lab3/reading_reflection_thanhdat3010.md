# Lab03 H3 - Reading notes and reflection draft

Prepared by Codex for Truong Thanh Dat to read, verify and rewrite in his own
words. This file does not certify that Dat has completed the reading.

## Required reading

| Source | Main idea | Check against this repository |
|---|---|---|
| [I - Codebase](https://12factor.net/codebase) | Track an application's codebase in version control across deployments. | Work on branches and preserve the Issue/PR trail. |
| [II - Dependencies](https://12factor.net/dependencies) | Explicitly declare and isolate dependencies. | Review `pyproject.toml`, pinned `requirements.txt` and a virtual environment. |
| [III - Config](https://12factor.net/config) | Separate deployment configuration from source using environment variables. | Compare monolith constants with `config.py`, `.env.example` and `.gitignore`. |
| [XI - Logs](https://12factor.net/logs) | Emit event streams and let the execution environment collect them. | JSON logs use stderr as required by Lab03, preserving stdout for CLI answers. Twelve-Factor's original example uses stdout. |
| [Packaging Python Projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/) | Use project metadata, a build backend and an importable package layout. | Identify `[build-system]`, `[project]`, the `src/assistant_core` layout and editable installation. Publishing to PyPI is not required here. |

## Reflection draft

The most visible violation is factor III, Config: the monolith places fee
settings and a sample credential in source, so changing deployment settings
requires a code change and may expose credentials. The refactored repository
provides an environment loader and `.env.example`, with `.env` excluded from
Git. The help extension introduces no additional secret or configuration.

Factor XI also matters: debug prints mixed with answers make the CLI harder
to use. Structured metadata logging to stderr separates operational events
from stdout answers. The H1 tests check this separation for help responses.

Limit: do not state that the whole service is perfectly configured. The
existing CLI constructs `AssistantService()` without explicitly calling
`load_settings()`, and the service retains fallback defaults. Verify the
actual entry point before claiming environment settings are applied end to
end; fixing the team's configuration wiring is outside this help PR.

## Dat's checklist

- [ ] Read all five linked sources and inspect the referenced files.
- [ ] Choose the factor you consider most violated and justify your choice.
- [ ] Rewrite the reflection in your own words, using one concrete example.
- [ ] Distinguish changes already present in the team repository from changes
  you personally made. Do not claim ownership of teammates' refactoring.
