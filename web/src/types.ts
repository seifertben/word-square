export interface FixedCell {
  fixed: string;
}

export interface BlockedCell {
  blocked: true;
}

export interface Board {
  date: string;
  size: number;
  minWordLength: number;
  grid: (FixedCell | BlockedCell | null)[][];
  /** The completed square's across-words, one per row (powers Reveal). */
  solution: string[];
}

export interface Pos {
  row: number;
  col: number;
}
