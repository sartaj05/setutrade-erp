# Testing guide

## Client acceptance workflow

The Django acceptance suite covers the client-demo golden path:

`login → role context → customer → quotation → order → stock reservation → invoice → UPI payment → delivery OTP/e-POD → ledger`

It also performs a sidebar API regression smoke test across the staff modules.

Run it from the backend directory:

```bash
python manage.py test api.tests.ProductionApiTests
```

Run the complete local validation:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

The same backend tests and frontend production build run in `.github/workflows/ci.yml` for pushes and pull requests.
