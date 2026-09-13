import { useEffect } from "react";
import { Confetti } from "./Confetti";

interface WinOverlayProps {
  elapsed: number;
  onClose: () => void;
}

function fmt(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function WinOverlay({ elapsed, onClose }: WinOverlayProps) {
  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [onClose]);

  return (
    <div
      className="win-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="win-title"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <Confetti active />
      <div className="win-card">
        <button className="win-close" type="button" onClick={onClose} aria-label="Close">
          &times;
        </button>
        <h2 id="win-title">Square complete!</h2>
        <p>You filled every row and column with a valid word in {fmt(elapsed)}.</p>
        <button className="win-dismiss" type="button" onClick={onClose}>
          View completed square
        </button>
      </div>
    </div>
  );
}
