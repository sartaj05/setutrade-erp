# Validation record — Growth v4

The packaging environment cannot reach npm/PyPI registries, so a clean dependency install and full Django/Vite/Expo runtime build cannot be executed locally in this session.

Checks run before packaging:

- Python compilation for the entire `backend/` tree: passed
- `node --check` for the new non-JSX strategic demo-data module: passed
- Structural delimiter check for `StrategicModulePage.jsx`: passed
- `git diff --check`: passed
- No merge-conflict markers found in tracked source files
- Migration filenames are continuous from `0001` through `0042`
- Ten Growth v4 feature commits exist for Phases 17–26
- Growth v4 seed data and backend smoke tests were added
- Git working tree is required to be clean before release packaging

GitHub CI remains the authoritative connected-runner validation and runs:

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
python manage.py seed_demo
python manage.py test
npm install && npm run build
npm install && npx expo config --type public
```

A green CI run is required before real client go-live.
