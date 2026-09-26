# Submission checklist

## Current local edition — 2026-09-24

- [x] Version 0.2.0 continuing journeys and classic-save compatibility implemented.
- [x] 110 local tests and Ruff checks pass after the unified-menu update.
- [x] Fresh temporary Python 3.12 editable installation, tests and module launch pass.
- [x] README, progression rules, endings and development feedback updated.
- [ ] Player has accepted new progression balance and second-journey controls.
- [ ] Latest implementation uploaded and that exact revision passes Ubuntu CI.

The earlier release had a public repository and passing CI. Those historical
results do not verify the new continuing-journey code. The final-delivery checks
below must be confirmed against the version actually submitted.

## Final-delivery checks

- [x] Installable Python 3.10+ package with module entry point.
- [x] Local Git baseline preserves the existing prototype honestly.
- [x] README explains play, commands, saves and limitations.
- [x] Unit tests cover branches, inventory effects and save replay.
- [x] Ubuntu 24.04 CI workflow configured for Python 3.10 and 3.12.
- [ ] CI actually executed successfully on GitHub (configuration is not a result).
- [ ] Public GitHub repository created and local commits pushed.
- [ ] Fresh clone of the public repository installed and played.
- [ ] Student reviewed core code and course AI-assistance policy.
- [ ] Current Moodle deadline and submission instructions checked.
- [ ] Public repository URL submitted on Moodle and receipt confirmed.

Do not mark remote checks complete based only on local testing.
