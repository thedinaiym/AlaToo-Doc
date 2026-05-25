"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

const TEMP_UNIVERSITY_ID = "123";
const TEMP_PASSWORD = "123";

export default function LoginPage() {
  const router = useRouter();
  const [universityId, setUniversityId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (universityId === TEMP_UNIVERSITY_ID && password === TEMP_PASSWORD) {
      localStorage.setItem("access_token", "temporary-dev-token");
      router.push("/");
      return;
    }

    setError("Invalid university ID or password.");
  }

  return (
    <section className="flex min-h-[calc(100vh-78px)] items-center justify-center px-4 py-10 sm:px-6 lg:px-8">
      <div className="w-full max-w-md rounded-lg border border-gray-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-gray-900">Sign in to Alatoo-Doc</h1>
          <p className="mt-2 text-sm text-gray-600">
            Use your university credentials to access the portal.
          </p>
        </div>

        <form className="space-y-5" onSubmit={handleSubmit}>
          <div>
            <label
              htmlFor="university_id"
              className="block text-sm font-medium text-gray-700"
            >
              University ID
            </label>
            <input
              id="university_id"
              name="university_id"
              type="text"
              autoComplete="username"
              required
              value={universityId}
              onChange={(event) => setUniversityId(event.target.value)}
              className="mt-2 block w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 outline-none transition placeholder:text-gray-400 focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
              placeholder="Enter your university ID"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700"
            >
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-2 block w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 outline-none transition placeholder:text-gray-400 focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
              placeholder="Enter your password"
            />
          </div>

          {error ? (
            <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            className="w-full rounded-md bg-blue-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2"
          >
            Sign In
          </button>
        </form>
      </div>
    </section>
  );
}
