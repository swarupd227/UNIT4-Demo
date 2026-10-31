# Unit4 CR to ERPx Migration Studio

Demo workbench for Unit4 AI Transformation RFP use case 1. All customer material is synthetic.

## Run it

Requires Docker Desktop. Node is only used for the shortcuts below.

```bash
npm run dev
```

In a second terminal, the first time and whenever the data should be rebuilt:

```bash
npm run seed
```

- Web: http://localhost:5183
- API: http://localhost:8000/docs
- Postgres: `localhost:5544` (user, password and database are all `studio`)

## Checks

```bash
npm run verify
```

```bash
npm run test:api
```

```bash
npm run lint:api
```

```bash
npm run test:web
```

```bash
npm run lint:web
```

If a hand-authored agent result is reviewed against a changed input, record that with:

```bash
docker compose run --rm api python -m engines.agents.stamp
```

See [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) for the plan and spec decisions.
