"use client"

import { createContext, useContext, useState, ReactNode } from "react";

interface AppContextType {
    isSearchOpen: boolean;
    toggleSearch: () => void;
    searchQuery: string;
    setSearchQuery: (q: string) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppContextProvider({ children }: { children: ReactNode }) {
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    const toggleSearch = () => setIsSearchOpen((prev) => !prev);

    return (
        <AppContext.Provider value={{ isSearchOpen, toggleSearch, searchQuery, setSearchQuery }}>
            {children}
        </AppContext.Provider>
    );
}

export function useApp() {
    const context = useContext(AppContext);
    if (!context) throw new Error("useApp must be used within an AppContextProvider");
    return context;
}