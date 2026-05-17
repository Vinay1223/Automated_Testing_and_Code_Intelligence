export default function ReposPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold">Repositories</h1>
      <p className="mt-2 text-zinc-500">
        Install the CodeIntel GitHub App on the repos you want covered. Once
        installed they appear here automatically.
      </p>
      <a
        href={process.env.NEXT_PUBLIC_GITHUB_APP_INSTALL_URL ?? '#'}
        className="mt-6 inline-block rounded-lg bg-brand-500 px-5 py-3 text-white hover:bg-brand-600"
      >
        Install GitHub App
      </a>
    </div>
  );
}
