"use client";

import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import { usePathname } from "next/navigation";

interface SearchContextValue {
  search: string;
  setSearch: (value: string) => void;
}

const SearchContext = createContext<SearchContextValue>({ search: "", setSearch: () => {} });

export function SearchProvider({ children }: { children: ReactNode }) {
  const [search, setSearch] = useState("");
  const pathname = usePathname();

  // Clear search on navigation
  useEffect(() => {
    setSearch("");
  }, [pathname]);

  return (
    <SearchContext.Provider value={{ search, setSearch }}>
      {children}
    </SearchContext.Provider>
  );
}

export function useSearch() {
  return useContext(SearchContext);
}
