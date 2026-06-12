import Link from "next/link";
import React from "react";

export default function Logo() {
  return (
    <div className="shrink-0 flex items-center">
      <Link
        href="/"
        className="text-3xl font-extrabold tracking-tight font-heading text-foreground group transition-all"
      >
        Blog
        <span className="text-primary group-hover:opacity-80 transition-opacity">
          .
        </span>
      </Link>
    </div>
  );
}
