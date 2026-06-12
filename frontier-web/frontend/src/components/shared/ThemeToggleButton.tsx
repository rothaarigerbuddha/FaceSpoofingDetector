"use client";

import React, { useState, useEffect } from 'react';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';

export default function ThemeToggleButton() {
  const [mounted, setMounted] = useState(false);
  const { resolvedTheme, setTheme } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <button 
        aria-hidden="true"
        className="w-10 h-10 p-2 text-transparent rounded-full flex items-center justify-center pointer-events-none"
      >
        <Sun className="h-5 w-5 opacity-0" />
      </button>
    );
  }

  return (
    <button
      onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
      aria-label="Toggle Dark Mode"
      type="button"
      className="w-10 h-10 p-2 text-foreground hover:text-primary hover:bg-muted/50 transition-all rounded-full flex items-center justify-center relative select-none"
    >
      <Sun className="h-5 w-5 transition-all transform scale-100 rotate-0 dark:-rotate-90 dark:scale-0 pointer-events-none" />
      <Moon className="h-5 w-5 transition-all transform scale-0 rotate-90 dark:rotate-0 dark:scale-100 absolute pointer-events-none" />
      <span className="sr-only">Toggle theme</span>
    </button>
  );
}
