import Image from "next/image";
import Link from "next/link";

export default function Header() {
  return (
    <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
      <Link href="/dashboard" className="text-xl font-bold text-blue-700">
        Alatoo-Doc
      </Link>

      <nav className="hidden items-center gap-4 text-sm font-medium text-gray-600 md:flex">
        <Link className="transition hover:text-blue-700" href="/dashboard">
          Dashboard
        </Link>
        <Link className="transition hover:text-blue-700" href="/dashboard/create">
          Create
        </Link>
        <Link className="transition hover:text-blue-700" href="/dashboard/inbox">
          Inbox
        </Link>
        <Link className="transition hover:text-blue-700" href="/dashboard/outbox">
          Outbox
        </Link>
        <Link
          className="rounded-md border border-gray-300 px-3 py-1.5 transition hover:bg-gray-50"
          href="/login"
        >
          Login
        </Link>
      </nav>

      <Image
        src="/logo.png"
        width={130}
        height={45}
        alt="University logo"
        priority
      />
    </header>
  );
}
