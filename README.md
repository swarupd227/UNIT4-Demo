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

- Web: http://localhost:5183, or http://localhost:5184 with `npm run demo`, the production build for presenting
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

Browser tests run against the production build, with the journey, accessibility audit and timings:

```bash
npm run e2e
```

To record the scene fallbacks. Run this before `npm run demo`, because the build includes them:

```bash
npm run record
```

If a hand-authored agent result is reviewed against a changed input, record that with:

```bash
docker compose run --rm api python -m engines.agents.stamp
```

See [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) for the plan and spec decisions.
