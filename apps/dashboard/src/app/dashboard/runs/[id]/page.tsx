import { apiFetch } from '@/lib/api';
import { notFound } from 'next/navigation';

interface TestRun {
  id: string;
  state: string;
  framework: string;
  target: { name: string; qualified_name: string; raises: string[] };
  final_test_code: string | null;
  final_explanation: string | null;
  error: string | null;
  attempts: { attempt: number; provider: string; model: string; sandbox_passed: boolean | null }[];
}

export default async function RunDetail({ params }: { params: { id: string } }) {
  let run: TestRun;
  try {
    run = await apiFetch<TestRun>(`/v1/runs/${params.id}`);
  } catch {
    notFound();
  }
  return (
    <div className="max-w-4xl">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold">{run!.target.qualified_name}</h1>
        <span
          className={
            'rounded-full px-2 py-1 text-xs ' +
            (run!.state === 'passed'
              ? 'bg-emerald-100 text-emerald-700'
              : run!.state === 'failed'
                ? 'bg-rose-100 text-rose-700'
                : 'bg-zinc-100 text-zinc-700')
          }
        >
          {run!.state}
        </span>
      </div>
      {run!.final_explanation && (
        <p className="mt-2 text-sm text-zinc-500">{run!.final_explanation}</p>
      )}
      <h2 className="mt-8 text-lg font-semibold">Attempts</h2>
      <ol className="mt-2 space-y-2">
        {run!.attempts.map((a) => (
          <li
            key={a.attempt}
            className="rounded-lg border border-zinc-200 p-3 text-sm dark:border-zinc-800"
          >
            <div className="font-mono">
              #{a.attempt} · {a.provider}/{a.model}
            </div>
            <div className="text-zinc-500">
              sandbox: {a.sandbox_passed === null ? 'pending' : a.sandbox_passed ? 'passed' : 'failed'}
            </div>
          </li>
        ))}
      </ol>
      {run!.final_test_code && (
        <>
          <h2 className="mt-8 text-lg font-semibold">Generated test</h2>
          <pre className="mt-2 overflow-x-auto rounded-xl bg-zinc-900 p-4 text-xs text-zinc-100">
            <code>{run!.final_test_code}</code>
          </pre>
        </>
      )}
      {run!.error && (
        <div className="mt-6 rounded-xl bg-rose-50 p-4 text-sm text-rose-800">{run!.error}</div>
      )}
    </div>
  );
}
