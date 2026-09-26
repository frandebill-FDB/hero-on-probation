# Submission checklist

## Verified evidence — 2026-09-26

- [x] Public repository: [hero-on-probation](https://github.com/frandebill-FDB/hero-on-probation).
- [x] Python 3.10+ package with `pyproject.toml`, a build backend and module entry point.
- [x] README documents installation, controls, saving and verification.
- [x] Multiple modules and reusable `Hero` / `Journey` types are available for import.
- [x] The uploaded gameplay revision `94d1a5d` passed
  [Ubuntu 24.04 CI on Python 3.10 and 3.12](https://github.com/frandebill-FDB/hero-on-probation/actions/runs/36240490429).
- [x] A fresh public clone of that revision installed with `uv pip install -e .`,
  launched with `uv run -m hero_on_probation`, completed two journeys and passed
  all 139 tests in an isolated Python 3.12 environment.
- [x] The author reported playtesting the current game without encountering a bug.
  This is a playtest result, not a guarantee that every path is bug-free.

The final documentation/style cleanup is verified separately below. Earlier CI
results are evidence for their named revision, not for later code changes.

## Final cleanup verification

- [x] Updated documentation and local links checked; all 140 local tests pass.
- [x] Ruff `E`, `W`, `F` and `I` checks and formatting pass with an 88-character
  line-length limit. Earlier overlong source lines have been split.
- [x] Syntax-tree comparison confirms that source changes affect only two game
  messages and the package description; rewrapping leaves gameplay logic intact.
- [x] Code/style cleanup revision `7effb5e` uploaded and passed
  [GitHub Actions on Python 3.10 and 3.12](https://github.com/frandebill-FDB/hero-on-probation/actions/runs/36242984719),
  including installation, all 140 tests, module launch and stricter style checks.

These links identify the verified code revisions. Subsequent documentation-only
updates can also be checked in the repository's
[Actions history](https://github.com/frandebill-FDB/hero-on-probation/actions/workflows/test.yml).

## Student's remaining submission steps

- [ ] Finish reviewing and updating the development log and feedback record.
- [ ] Review the core code and confirm the course's AI-assistance rules.
- [ ] Check the current deadline and submission instructions on Moodle.
- [ ] Submit the public repository URL on Moodle and retain the confirmation.

Submit the repository URL, not a local directory or a GitHub Actions link.
A successful GitHub upload is not a Moodle submission.
