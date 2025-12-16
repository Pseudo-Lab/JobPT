import Link from "next/link";
import React from "react";

const AppHeader = () => (
  <header className="bg-[#f6f7fb] border-b border-slate-200">
    <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6 sm:px-12">
      <Link href="/" className="flex items-center gap-3" aria-label="JobPT 홈으로 이동">
        <div className="h-10 w-10 rounded-full bg-[rgb(96,150,222)] shadow-sm" />
        <span className="text-xl font-semibold tracking-tight text-slate-800 sm:text-2xl">
          JobPT
        </span>
      </Link>
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[rgba(96,150,222,0.2)] text-[rgb(96,150,222)] shadow-sm">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="h-5 w-5"
          aria-hidden="true"
        >
          <circle cx="12" cy="8.5" r="3" />
          <path d="M5.5 19a5.5 5.5 0 015.5-5.5h2a5.5 5.5 0 015.5 5.5v.5a1.5 1.5 0 01-1.5 1.5H7a1.5 1.5 0 01-1.5-1.5V19z" />
        </svg>
      </div>
    </div>
  </header>
);

export default AppHeader;
