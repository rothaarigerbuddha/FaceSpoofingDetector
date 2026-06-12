"use client";

import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useDebounce } from "@/hooks/use-debounce";

export function ArticleSearch() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";
  
  const [searchTerm, setSearchTerm] = useState(initialQuery);
  const debouncedSearch = useDebounce(searchTerm, 500);

  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isMounted) return;

    const params = new URLSearchParams(searchParams.toString());
    
    // Check if the current URL parameter matches the debounced string
    // to avoid unnecessary router pushes
    const currentQ = params.get("q") || "";

    if (debouncedSearch && debouncedSearch !== currentQ) {
      params.set("q", debouncedSearch);
      params.set("page", "1"); // Reset to page 1 on new search
      router.push(`?${params.toString()}`);
    } else if (!debouncedSearch && currentQ) {
      params.delete("q");
      params.set("page", "1");
      router.push(`?${params.toString()}`);
    }
  }, [debouncedSearch, router, searchParams, isMounted]);

  return (
    <div className="relative w-full max-w-sm">
      <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
      <Input
        type="search"
        placeholder="Search articles..."
        className="pl-8"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
    </div>
  );
}
