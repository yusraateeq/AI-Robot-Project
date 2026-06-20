"use client";

import LiveLine from "./LiveLine";

interface NavbarProps {
  title: string;
}

export default function Navbar({ title }: NavbarProps) {
  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-border-soft bg-panel/80 px-5 pl-16 backdrop-blur-md md:pl-5">
      <h1 className="text-sm font-semibold tracking-tight text-text-primary">
        {title}
      </h1>

      <div className="hidden md:block">
        <LiveLine />
      </div>

      <div className="flex items-center gap-3">
        <span className="flex items-center gap-1.5 rounded-full border border-signal/30 bg-signal/10 px-2.5 py-1 text-xs font-medium text-signal">
          <span className="signal-dot h-1.5 w-1.5 rounded-full bg-signal" />
          Live
        </span>
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-panel-raised text-xs font-medium text-text-secondary">
          AD
        </div>
      </div>
    </header>
  );
}