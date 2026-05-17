'use client';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const data = Array.from({ length: 12 }, (_, i) => ({
  day: `D-${11 - i}`,
  pct: 60 + Math.round(Math.random() * 35),
}));

export default function CoveragePage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold">Static coverage</h1>
      <p className="mt-2 text-zinc-500">
        % of public functions across your active repos that have at least one
        test mentioning their name. Replace with line coverage by uploading a
        coverage.xml in your CI.
      </p>
      <div className="mt-8 h-72 rounded-2xl border border-zinc-200 p-4 dark:border-zinc-800">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="day" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Line type="monotone" dataKey="pct" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
