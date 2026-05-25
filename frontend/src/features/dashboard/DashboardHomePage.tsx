"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import type { User } from "@/src/types";

type Action = {
  title: string;
  description: string;
  href: string;
  label: string;
};

const ROLE_ACTIONS: Record<string, Action[]> = {
  student: [
    {
      title: "Create Application",
      description: "Prepare an application, generate text with AI, and send it to a dean.",
      href: "/dashboard/create",
      label: "Create",
    },
    {
      title: "Outbox",
      description: "Track submitted applications and open generated PDF documents.",
      href: "/dashboard/outbox",
      label: "Open Outbox",
    },
  ],
  dean: [
    {
      title: "Inbox",
      description: "Review pending student applications, sign, or reject documents.",
      href: "/dashboard/inbox",
      label: "Review",
    },
  ],
  admin: [
    {
      title: "Mass Distribution",
      description: "Send an official document to all students in a selected faculty.",
      href: "/dashboard/admin/broadcast",
      label: "Broadcast",
    },
    {
      title: "Outbox",
      description: "View documents created from your administrator account.",
      href: "/dashboard/outbox",
      label: "Open Outbox",
    },
  ],
};

export default function DashboardHomePage() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    queueMicrotask(() => {
      const token = localStorage.getItem("access_token");
      const storedUser = localStorage.getItem("current_user");

      if (!token || !storedUser) {
        router.replace("/login");
        return;
      }

      setCurrentUser(JSON.parse(storedUser) as User);
      setIsReady(true);
    });
  }, [router]);

  if (!isReady || !currentUser) {
    return (
      <section className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="rounded-lg border border-gray-200 bg-white p-5 text-sm text-gray-600 shadow-sm">
          Loading dashboard...
        </div>
      </section>
    );
  }

  const actions = ROLE_ACTIONS[currentUser.role] ?? [];

  return (
    <section className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-medium capitalize text-blue-700">
          {currentUser.role} dashboard
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-gray-950">
          {currentUser.full_name}
        </h1>
        <p className="mt-2 text-sm text-gray-600">
          University ID: {currentUser.university_id}
          {currentUser.faculty ? ` · ${currentUser.faculty}` : ""}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {actions.map((action) => (
          <div
            key={action.href}
            className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
          >
            <h2 className="text-lg font-semibold text-gray-950">{action.title}</h2>
            <p className="mt-2 min-h-12 text-sm leading-6 text-gray-600">
              {action.description}
            </p>
            <Link
              href={action.href}
              className="mt-5 inline-flex rounded-md bg-blue-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-800"
            >
              {action.label}
            </Link>
          </div>
        ))}
      </div>
    </section>
  );
}
