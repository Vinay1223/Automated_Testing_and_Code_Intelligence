import { apiFetch } from '@/lib/api';
import Link from 'next/link';

interface RunSummary {
  id: string;
  function: string;
  framework: string;
  state: string;
  attempts: number;
  passed: boolean;
  updated_at: string;
}

export default async function RunsPage() {
  const runs = await apiFetch<RunSummary[]>('/v1/runs').catch(() => []);
  return (
    <div>
      <h1 className="text-2xl font-semibold">Runs</h1>
      <table className="mt-6 w-full text-sm">
        <thead className="text-left text-zinc-500">
          <tr>
            <th className="py-2">Function</th>
            <th>Framework</th>
            <th>State</th>
            <th className="text-right">Attempts</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {runs.map((r) => (
            <tr key={r.id} className="border-t border-zinc-200 dark:border-zinc-800">
              <td className="py-2 font-mono">{r.function}</td>
              <td>{r.framework}</td>
              <td>{r.state}</td>
              <td className="text-right">{r.attempts}</td>
              <td className="text-right">
                <Link className="text-brand-500 hover:underline" href={`/dashboard/runs/${r.id}`}>
                  open
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
