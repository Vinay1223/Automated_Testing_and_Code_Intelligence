import Link from 'next/link';

export default function MarketingHome() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-24">
      <h1 className="text-5xl font-bold tracking-tight">
        Tests, written by your repo&apos;s AI engineer.
      </h1>
      <p className="mt-6 text-lg text-zinc-600 dark:text-zinc-400">
        CodeIntel scans every PR, finds untested functions, generates pytest
        and Jest suites, runs them in a sandboxed container, and opens a
        cleaned-up PR back to your repo. Pay only for what you ship.
      </p>
      <div className="mt-10 flex gap-4">
        <Link
          href="/sign-up"
          className="rounded-lg bg-brand-500 px-5 py-3 text-white hover:bg-brand-600"
        >
          Start free
        </Link>
        <Link
          href="/sign-in"
          className="rounded-lg border border-zinc-200 px-5 py-3 dark:border-zinc-800"
        >
          Sign in
        </Link>
      </div>
      <section className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-3">
        {features.map((f) => (
          <div
            key={f.title}
            className="rounded-2xl border border-zinc-200 p-6 dark:border-zinc-800"
          >
            <h3 className="font-semibold">{f.title}</h3>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">{f.body}</p>
          </div>
        ))}
      </section>
    </main>
  );
}

const features = [
  {
    title: 'PR-aware GitHub App',
    body: 'Only generates tests for the functions that actually changed. Zero spam.',
  },
  {
    title: 'Sandboxed validation',
    body: 'Every generated test runs in a Dockerized sandbox with no network and tight CPU/memory caps.',
  },
  {
    title: 'BYO-LLM',
    body: 'Use our Groq tier or route through your own AWS Bedrock / Azure OpenAI. Your code stays in your cloud.',
  },
];
