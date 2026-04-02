"use client";

import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import { usePathname } from "next/navigation";

interface ToolbarContextValue {
  toolbarContent: ReactNode | null;
  setToolbarContent: (content: ReactNode | null) => void;
  titlePrefix: string | null;
  setTitlePrefix: (prefix: string | null) => void;
}

const ToolbarContext = createContext<ToolbarContextValue>({
  toolbarContent: null,
  setToolbarContent: () => {},
  titlePrefix: null,
  setTitlePrefix: () => {},
});

export function ToolbarProvider({ children }: { children: ReactNode }) {
  const [toolbarContent, setToolbarContent] = useState<ReactNode | null>(null);
  const [titlePrefix, setTitlePrefix] = useState<string | null>(null);
  const pathname = usePathname();

  useEffect(() => {
    setToolbarContent(null);
    setTitlePrefix(null);
  }, [pathname]);

  return (
    <ToolbarContext.Provider value={{ toolbarContent, setToolbarContent, titlePrefix, setTitlePrefix }}>
      {children}
    </ToolbarContext.Provider>
  );
}

export function useToolbar() {
  return useContext(ToolbarContext);
}

/** Mount content into the topbar. Cleans up on unmount. */
export function ToolbarSlot({ children, count }: { children: ReactNode; count?: number | string }) {
  const { setToolbarContent, setTitlePrefix } = useToolbar();

  useEffect(() => {
    setToolbarContent(children);
  }, [children, setToolbarContent]);

  useEffect(() => {
    if (count !== undefined) setTitlePrefix(String(count));
    return () => setTitlePrefix(null);
  }, [count, setTitlePrefix]);

  useEffect(() => {
    return () => setToolbarContent(null);
  }, [setToolbarContent]);

  return null;
}
