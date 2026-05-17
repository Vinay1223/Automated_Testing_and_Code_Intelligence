import Link from 'next/link';
import { UserButton } from '@clerk/nextjs';
import { LayoutDashboard, GitBranch, Activity, BarChart3, CreditCard } from 'lucide-react';

const links = [
  { href: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { href: '/dashboard/repos', label: 'Repos', icon: GitBranch },
  { href: '/dashboard/runs', label: 'Runs', icon: Activity },
  { href: '/dashboard/coverage', label: 'Coverage', icon: BarChart3 },
  { href: '/dashboard/billing', label: 'Billing', icon: CreditCard },
];

export function Nav() {
  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-zinc-200 p-4 dark:border-zinc-800">
      <div className="mb-8 text-lg font-semibold">CodeIntel</div>
      <nav className="flex-1 space-y-1">
        {links.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm hover:bg-zinc-100 dark:hover:bg-zinc-900"
          >
            <l.icon className="h-4 w-4" />
            {l.label}
          </Link>
        ))}
      </nav>
      <div className="mt-4">
        <UserButton afterSignOutUrl="/" />
      </div>
    </aside>
  );
}
