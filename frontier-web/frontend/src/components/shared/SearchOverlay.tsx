"use client"

import React, { useEffect, useRef, useState } from 'react'
import { cn } from '@/lib/utils'
import { useApp } from '@/providers/AppContextProvider'
import { useRouter } from 'next/navigation'
import { X, Search } from 'lucide-react'

const SearchOverlay = () => {
    const { isSearchOpen, toggleSearch } = useApp()
    const [query, setQuery] = useState('')
    const inputRef = useRef<HTMLInputElement>(null)
    const router = useRouter()

    // Focus input when opened
    useEffect(() => {
        if (isSearchOpen) {
            setTimeout(() => inputRef.current?.focus(), 50)
        } else {
            setQuery('')
        }
    }, [isSearchOpen])

    // Close on Escape
    useEffect(() => {
        const handleKey = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isSearchOpen) toggleSearch()
        }
        window.addEventListener('keydown', handleKey)
        return () => window.removeEventListener('keydown', handleKey)
    }, [isSearchOpen, toggleSearch])

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (!query.trim()) return
        router.push(`?q=${encodeURIComponent(query.trim())}`)
        toggleSearch()
    }

    return (
        <div
            onClick={toggleSearch}
            className={cn(
                'fixed inset-0 z-50 transition-all duration-300',
                isSearchOpen
                    ? 'opacity-100 pointer-events-auto'
                    : 'opacity-0 pointer-events-none'
            )}
            style={{ backdropFilter: 'blur(20px)', background: 'rgba(0,0,0,0.35)' }}
        >
            {/* Close button */}
            <button
                onClick={(e) => {
                    e.stopPropagation()
                    toggleSearch()
                }}
                className="absolute top-6 right-6 text-white/70 hover:text-white transition-colors p-2 rounded-full hover:bg-white/10"
                aria-label="Close search"
            >
                <X size={24} strokeWidth={1.5} />
            </button>

            {/* Search box */}
            <div
                onClick={(e) => e.stopPropagation()}
                className="flex flex-col justify-center h-full max-w-2xl mx-auto px-6"
            >
                <p className="text-white/40 text-xs uppercase tracking-[0.2em] mb-8 font-light">
                    Start typing to search
                </p>

                <form onSubmit={handleSubmit} className="relative group">
                    {/* Search icon */}
                    <Search
                        size={18}
                        strokeWidth={1.5}
                        className="absolute left-0 top-1/2 -translate-y-1/2 text-white/40 group-focus-within:text-white transition-colors duration-200"
                    />

                    <input
                        ref={inputRef}
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search articles, topics..."
                        className={cn(
                            'w-full pl-8 pr-4 py-4 bg-transparent',
                            'text-white text-2xl font-light placeholder:text-white/25',
                            'border-b border-white/20 focus:border-white/70',
                            'outline-none transition-colors duration-300',
                            'caret-white'
                        )}
                    />

                    {/* Animated underline */}
                    <span className="absolute bottom-0 left-0 h-px w-0 bg-white group-focus-within:w-full transition-all duration-500 ease-out" />
                </form>

                {/* Hit enter hint */}
                {query && (
                    <p className="mt-4 text-white/30 text-xs tracking-widest uppercase">
                        Press <kbd className="px-1.5 py-0.5 rounded border border-white/20 text-white/50 font-mono text-[10px]">Enter</kbd> to search
                    </p>
                )}
            </div>
        </div>
    )
}

export default SearchOverlay