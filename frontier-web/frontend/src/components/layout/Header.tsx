"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Search, Menu, ChevronRight } from 'lucide-react';
import ThemeToggleButton from '../shared/ThemeToggleButton';
import SearchOverlay from '../shared/SearchOverlay';
import { useApp } from '@/providers/AppContextProvider';
import Logo from '../shared/Logo';

export default function Header({ isLoggedIn }: { isLoggedIn: boolean }) {
  const [isScrolled, setIsScrolled] = useState(false);
  const { toggleSearch } = useApp();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header 
  className={`sticky top-0 z-50 w-full border-b transition-[padding,background-color,box-shadow,border-color] duration-300 ease-in-out ${
    isScrolled 
      ? 'bg-background/90 backdrop-blur-md shadow-sm border-border/50 dark:border-border/50 py-3' 
      : 'bg-background border-transparent py-5'
  }`}
>
      <div className="container mx-auto">
        <div className="flex items-center justify-between">
          
          {/* Logo */}
          <Logo />

          <nav className="hidden md:flex  flex-1 justify-center space-x-12 font-heading">
             <Link href="/" className="relative font-playfair text-foreground hover:text-primary transition-colors text-base font-medium duration-200 group">
               Home
               <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all duration-300 group-hover:w-full"></span>
             </Link>

             {isLoggedIn ? (
               <Link href="/dashboard" className="relative font-playfair text-foreground hover:text-primary transition-colors text-base font-medium duration-200 group">
                 Dashboard
                 <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all duration-300 group-hover:w-full"></span>
               </Link>
             ) : (
               <Link href="/login" className="relative font-playfair text-foreground hover:text-primary transition-colors text-base font-medium duration-200 group">
                 Login
                 <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all duration-300 group-hover:w-full"></span>
               </Link>
             )}
          </nav>

          {/* Right section (Subscribe, Theme, Search, Mobile) */}
          <div className="flex items-center space-x-2 md:space-x-4">
             
             <button aria-label="Search" onClick={() => toggleSearch()} className="p-2 text-foreground hover:text-primary transition-colors rounded-full hover:bg-muted duration-200">
               <Search className="h-5 w-5" />
             </button>

             

             <ThemeToggleButton />

             {/* Mobile menu button */}
             <div className="md:hidden pl-2">
               <button aria-label="Menu" className="p-2 text-foreground hover:text-primary transition-colors rounded-full hover:bg-muted duration-200">
                 <Menu className="h-6 w-6" />
               </button>
             </div>
          </div>
        </div>
      </div>
      <SearchOverlay />
    </header>
  );
}
