import Link from "next/link";

export default function HomePage() {
  return (
    <section className="mx-auto flex min-h-[calc(100vh-78px)] max-w-5xl flex-col items-center justify-center px-6 text-center">
      <h1 className="text-4xl font-bold text-gray-900">Welcome to Alatoo-Doc</h1>
      <p className="mt-4 max-w-2xl text-base text-gray-600">
        Manage university documents, signatures, and approvals in one place.
      </p>

      <Link
        href="/login"
        className="mt-8 rounded-md bg-blue-700 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-800"
      >
        Go to Login
      </Link>
    </section>
  );
}
