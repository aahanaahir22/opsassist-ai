# Contributing

Use Python 3.12 and Node 22. Start from a focused issue, keep public-demo behavior simulator-only, add tests for every numerical or policy change, and do not commit secrets, databases, model caches, or generated indexes. Run `pytest apps/api/tests -q`, `npm run lint`, `npx tsc --noEmit`, and `npm test` before opening a pull request. Evaluation changes must include the seed and an explanation of dataset changes.
