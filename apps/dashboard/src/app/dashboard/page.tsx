import { apiFetch } from '@/lib/api';

interface RunSummary {
  id: string;
  state: string;
  function: string;
  framework: string;
  attempts: number;
  passed: boolean;
  updated_at: string;
}

export default async function OverviewPage() {
  let runs: RunSummary[] = [];
  try {
    runs = await apiFetch<RunSummary[]>('/v1/runs');
  } catch (e) {
    return (
      <Empty
        title="Welcome to CodeIntel"
        body={`No runs yet. Install the GitHub App or run the CLI to get started.`}
      />
    );
  }
  const total = runs.length;
  const passed = runs.filter((r) => r.passed).length;
  const pct = total === 0 ? 0 : Math.round((100 * passed) / total);

  return (
    <div>
      <h1 className="text-2xl font-semibold">Overview</h1>
      <section className="mt-6 grid grid-cols-3 gap-4">
        <Stat label="Total runs" value={total} />
        <Stat label="Passing" value={`${passed} (${pct}%)`} />
        <Stat label="Open PRs" value="—" />
      </section>
      <section className="mt-10">
        <h2 className="mb-3 text-lg font-semibold">Recent runs</h2>
        <table className="w-full text-sm">
          <thead className="text-left text-zinc-500">
            <tr>
              <th className="py-2">Function</th>
              <th>Framework</th>
              <th>State</th>
              <th className="text-right">Attempts</th>
            </tr>
          </thead>
          <tbody>
            {runs.slice(0, 10).map((r) => (
              <tr key={r.id} className="border-t border-zinc-200 dark:border-zinc-800">
                <td className="py-2 font-mono">{r.function}</td>
                <td>{r.framework}</td>
                <td>{r.state}</td>
                <td className="text-right">{r.attempts}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-2xl border border-zinc-200 p-4 dark:border-zinc-800">
      <div className="text-sm text-zinc-500">{label}</div>
      <div className="mt-1 text-3xl font-bold">{value}</div>
    </div>
  );
}

function Empty({ title, body }: { title: string; body: string }) {
  return (
    <div className="mt-10 rounded-2xl border border-dashed border-zinc-300 p-10 text-center dark:border-zinc-800">
      <h1 className="text-xl font-semibold">{title}</h1>
      <p className="mt-2 text-zinc-500">{body}</p>
    </div>
  );
}
