# Validation record

The packaging environment cannot reach npm/PyPI registries, so a clean dependency install and full Django/Vite/Expo runtime build cannot be executed here.

Static validations run before packaging:

- Python compilation for the entire `backend/` tree: passed
- TypeScript parser/transpile syntax check across 29 JavaScript/JSX source files: passed
- `git diff --check`: passed
- Django migration filenames: continuous from `0001` through `0032`
- Git working tree checked clean before release tag/package

GitHub CI is configured to perform the authoritative runtime checks on a connected runner:

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
python manage.py seed_demo
python manage.py test
npm install && npm run build
npm install && npx expo config --type public
```

A green GitHub Actions run is required before putting real client business or payment data into the deployment.
