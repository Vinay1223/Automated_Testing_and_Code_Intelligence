import * as React from 'react';

const colors: Record<string, string> = {
  passed: 'bg-emerald-100 text-emerald-700',
  failed: 'bg-rose-100 text-rose-700',
  generating: 'bg-amber-100 text-amber-700',
  validating: 'bg-amber-100 text-amber-700',
  healing: 'bg-amber-100 text-amber-700',
  pending: 'bg-zinc-100 text-zinc-700',
  cancelled: 'bg-zinc-100 text-zinc-500',
};

export function StateChip({ state }: { state: string }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs ${colors[state] ?? colors.pending}`}>
      {state}
    </span>
  );
}
