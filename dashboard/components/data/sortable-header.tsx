"use client";

interface SortableHeaderProps {
  label: string;
  sortKey: string | null;
  currentSort: string;
  onSort: (sort: string) => void;
}

export function SortableHeader({ label, sortKey, currentSort, onSort }: SortableHeaderProps) {
  if (!sortKey) {
    return (
      <th className="px-5 py-3.5 text-left text-xs font-medium whitespace-nowrap" style={{ color: "var(--text-light)" }}>
        {label}
      </th>
    );
  }

  const isAsc = currentSort === sortKey;
  const isDesc = currentSort === `-${sortKey}`;

  function handleClick() {
    if (isDesc) onSort(sortKey!);
    else if (isAsc) onSort(`-${sortKey}`);
    else onSort(`-${sortKey}`);
  }

  return (
    <th className="px-5 py-3.5 text-left text-xs font-medium whitespace-nowrap" style={{ color: "var(--text-light)" }}>
      <button
        onClick={handleClick}
        className="flex items-center gap-1 hover:text-[var(--text)] transition-colors"
      >
        {label}
        {isAsc && <span className="text-[var(--accent)]">&#9650;</span>}
        {isDesc && <span className="text-[var(--accent)]">&#9660;</span>}
      </button>
    </th>
  );
}
