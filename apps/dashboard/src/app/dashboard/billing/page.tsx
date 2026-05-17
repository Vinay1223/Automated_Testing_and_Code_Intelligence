import { auth } from '@clerk/nextjs/server';

const TIERS = [
  {
    name: 'Free',
    price: '$0',
    blurb: '100 runs / month, mock provider only',
    cta: 'Current plan',
  },
  {
    name: 'Team',
    price: '$29 / seat / mo',
    blurb: 'Unlimited runs, Groq + OpenAI + Anthropic, GitHub App, IDE extension',
    cta: 'Upgrade',
  },
  {
    name: 'Enterprise',
    price: 'Contact sales',
    blurb: 'Self-hosted Helm chart, BYO-LLM (Bedrock / Azure), SSO, SOC 2',
    cta: 'Book a call',
  },
];

export default async function BillingPage() {
  const { orgId } = auth();
  return (
    <div>
      <h1 className="text-2xl font-semibold">Billing</h1>
      <p className="mt-1 text-sm text-zinc-500">
        Org: <span className="font-mono">{orgId ?? 'personal'}</span>
      </p>
      <section className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-3">
        {TIERS.map((tier) => (
          <div
            key={tier.name}
            className="rounded-2xl border border-zinc-200 p-6 dark:border-zinc-800"
          >
            <h2 className="text-lg font-semibold">{tier.name}</h2>
            <div className="mt-1 text-2xl font-bold">{tier.price}</div>
            <p className="mt-2 text-sm text-zinc-500">{tier.blurb}</p>
            <button className="mt-6 w-full rounded-lg bg-brand-500 px-4 py-2 text-white hover:bg-brand-600">
              {tier.cta}
            </button>
          </div>
        ))}
      </section>
    </div>
  );
}
