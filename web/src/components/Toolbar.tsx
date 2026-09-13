interface ToolbarProps {
  onCheck: () => void;
  onReveal: () => void;
  onClear: () => void;
  solved: boolean;
}

export function Toolbar({ onCheck, onReveal, onClear, solved }: ToolbarProps) {
  return (
    <div className="toolbar">
      <button type="button" onClick={onCheck} disabled={solved}>
        Check
      </button>
      <button type="button" onClick={onReveal} disabled={solved}>
        Reveal
      </button>
      <button type="button" onClick={onClear}>
        Clear
      </button>
    </div>
  );
}
