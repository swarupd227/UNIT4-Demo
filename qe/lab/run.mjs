// Runs Playwright tests against builds of the billing module, each on a fresh copy of the seeded database.
//
//   node run.mjs --builds baseline --runs 20            repeat runs of the baseline
//   node run.mjs --builds all --workers 1 --confirm 5   the fault check: a catch must fail on 5 fresh runs
//   node run.mjs --serve baseline --port 5280            serve one build for people to use
//
// Options: --tests <dir> (default /estate/tests/e2e), --overlay <dir> (candidate files laid over the
// suite), --grep <pattern>, --workers <n>, --out <file.jsonl>
import { spawn } from 'node:child_process';
import { copyFileSync, cpSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, symlinkSync, appendFileSync } from 'node:fs';
import { join } from 'node:path';

const args = Object.fromEntries(
  process.argv.slice(2).reduce((pairs, arg, i, all) => {
    if (arg.startsWith('--')) pairs.push([arg.slice(2), all[i + 1] && !all[i + 1].startsWith('--') ? all[i + 1] : 'true']);
    return pairs;
  }, []),
);

const BUILDS = '/builds';
const SEED = '/seed/billing.db';
const tests = args.tests ?? '/estate/tests/e2e';
const sleep = (ms) => new Promise((done) => setTimeout(done, ms));

function startModule(build, port, dir, extraEnv = {}) {
  mkdirSync(dir, { recursive: true });
  copyFileSync(SEED, join(dir, 'billing.db'));
  return spawn('dotnet', [join(BUILDS, build, 'Billing.Web.dll')], {
    cwd: join(BUILDS, build),
    env: {
      ...process.env,
      ASPNETCORE_URLS: `http://0.0.0.0:${port}`,
      Billing__Database: join(dir, 'billing.db'),
      ...extraEnv,
    },
    stdio: ['ignore', 'ignore', 'pipe'],
  });
}

async function waitHealthy(port, server) {
  for (let i = 0; i < 300; i++) {
    if (server.exitCode !== null) throw new Error(`module exited with ${server.exitCode}`);
    try {
      const response = await fetch(`http://127.0.0.1:${port}/health`);
      if (response.ok) return;
    } catch {}
    await sleep(100);
  }
  throw new Error('module did not start');
}

function suiteCopy(name) {
  const dir = `/tmp/suites/${name}`;
  rmSync(dir, { recursive: true, force: true });
  cpSync(tests, dir, { recursive: true, filter: (src) => !src.includes('node_modules') && !src.includes('test-results') });
  // Candidate tests and their test data, laid out like the suite, go over the copy.
  if (args.overlay) cpSync(args.overlay, dir, { recursive: true, filter: (src) => !src.endsWith('manifest.json') });
  symlinkSync('/lab/tests/node_modules', join(dir, 'node_modules'));
  return dir;
}

function collect(report) {
  const out = [];
  const walk = (suite) => {
    for (const spec of suite.specs ?? []) {
      for (const t of spec.tests) {
        const results = t.results ?? [];
        const last = results[results.length - 1];
        const error = results.find((r) => r.error)?.error?.message ?? null;
        out.push({
          title: spec.title,
          file: spec.file,
          status: { expected: 'passed', unexpected: 'failed', flaky: 'flaky', skipped: 'skipped' }[t.status] ?? t.status,
          attempts: results.length,
          durationMs: results.reduce((sum, r) => sum + (r.duration ?? 0), 0),
          // When and where the last attempt ran, so overlapping tests can be found afterwards.
          started: last?.startTime ?? null,
          worker: last?.workerIndex ?? null,
          error: error ? error.replace(/\u001b\[[0-9;]*m/g, '').split('\n').slice(0, 6).join('\n') : null,
          trace: results.flatMap((r) => r.attachments ?? []).find((a) => a.name === 'trace')?.path ?? null,
        });
      }
    }
    for (const child of suite.suites ?? []) walk(child);
  };
  for (const suite of report.suites ?? []) walk(suite);
  return out;
}

const escape = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

// A failure counts only if it repeats. Each confirming run starts from a fresh database, because a
// retry inside the same run finds the data already used by the failed attempt.
async function confirmed(build, index, port, suite) {
  const first = await runOnce(build, index, port, suite);
  const rounds = Number(args.confirm ?? 1);
  let failing = first.tests.filter((t) => t.status === 'failed');
  for (let round = 2; round <= rounds && failing.length; round++) {
    const grep = failing.map((t) => escape(t.title)).join('|');
    const again = await runOnce(build, `${index}-confirm${round}`, port, suite, grep);
    const stillFailing = new Set(again.tests.filter((t) => t.status === 'failed').map((t) => t.title));
    for (const test of failing) {
      test.attempts += 1;
      if (!stillFailing.has(test.title)) test.status = 'flaky';
    }
    failing = failing.filter((t) => stillFailing.has(t.title));
  }
  return first;
}

async function runOnce(build, index, port, suite, grepOverride = null) {
  const dir = `/tmp/runs/${build}-${index}`;
  rmSync(dir, { recursive: true, force: true });
  const server = startModule(build, port, dir);
  let stderr = '';
  server.stderr.on('data', (chunk) => (stderr += chunk));
  const started = Date.now();
  try {
    await waitHealthy(port, server);
    const reportFile = join(dir, 'report.json');
    const playwrightArgs = ['playwright', 'test', '--reporter=json'];
    if (grepOverride ?? args.grep) playwrightArgs.push('--grep', grepOverride ?? args.grep);
    if (args.files) playwrightArgs.push(...args.files.split(','));
    await new Promise((done) => {
      const child = spawn('npx', playwrightArgs, {
        cwd: suite,
        env: {
          ...process.env,
          BASE_URL: `http://127.0.0.1:${port}`,
          WORKERS: args.workers ?? '2',
          RETRIES: args.retries ?? '0',
          PLAYWRIGHT_JSON_OUTPUT_NAME: reportFile,
        },
        stdio: ['ignore', 'ignore', 'inherit'],
      });
      child.on('exit', done);
    });
    const report = JSON.parse(readFileSync(reportFile, 'utf8'));
    return { build, run: index, seconds: Math.round((Date.now() - started) / 100) / 10, tests: collect(report) };
  } catch (error) {
    return { build, run: index, error: String(error), log: stderr.slice(-2000), tests: [] };
  } finally {
    server.kill('SIGTERM');
  }
}

async function serve() {
  const port = Number(args.port ?? 5280);
  const server = startModule(args.serve, port, '/tmp/serve');
  server.stderr.pipe(process.stderr);
  await waitHealthy(port, server);
  console.log(`Serving ${args.serve} on port ${port}`);
  server.on('exit', (code) => process.exit(code ?? 0));
}

async function main() {
  if (args.serve) return serve();

  const available = readdirSync(BUILDS).sort();
  const builds = !args.builds || args.builds === 'all'
    ? available.filter((b) => (b !== 'baseline' || !args.builds) && !b.startsWith('release-'))
    : args.builds.split(',');
  for (const b of builds) if (!existsSync(join(BUILDS, b))) throw new Error(`no build called ${b}`);

  const runs = Number(args.runs ?? 1);
  const parallel = Number(args.parallel ?? 1);
  const jobs = builds.flatMap((build) => Array.from({ length: runs }, (_, i) => ({ build, index: i + 1 })));
  const out = args.out;
  if (out) mkdirSync(out.split('/').slice(0, -1).join('/') || '.', { recursive: true });

  let next = 0;
  const lane = async (laneNo) => {
    const suite = suiteCopy(`lane-${laneNo}`);
    while (next < jobs.length) {
      const job = jobs[next++];
      const result = await confirmed(job.build, job.index, 5300 + laneNo, suite);
      const failed = result.tests.filter((t) => t.status === 'failed').map((t) => t.title.split(' ')[0]);
      console.log(`${job.build} run ${job.index}: ${result.error ?? `${result.tests.length} tests, failed: ${failed.join(' ') || 'none'}`} (${result.seconds ?? '-'}s)`);
      if (out) appendFileSync(out, JSON.stringify(result) + '\n');
    }
  };
  await Promise.all(Array.from({ length: parallel }, (_, i) => lane(i)));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
