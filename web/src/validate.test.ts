import { incorrectCells, isWordSquare, validLines } from "./validate";
import type { Grid } from "./board";

function makeGrid(rows: string[]): Grid {
  return rows.map((row) => row.split("").map((ch) => (ch === "." ? null : ch)));
}

// A valid 6x6 double word square (rows and columns are all words).
const GOOD = ["SADHES", "AGRAFE", "DRAFFS", "HAFFET", "EFFETE", "SESTET"];
const badDict = new Set(GOOD);

describe("validate", () => {
  it("accepts a complete word square", () => {
    const grid = makeGrid(GOOD);
    expect(isWordSquare(6, grid, badDict, 6)).toBe(true);
  });

  it("accepts words written backwards", () => {
    const rows = ["SECALP", ...GOOD.slice(1)];
    const dictionary = new Set(["PLACES", ...GOOD.slice(1)]);
    for (let c = 0; c < 6; c++) {
      dictionary.add(rows.map((row) => row[c]).join(""));
    }
    expect(isWordSquare(6, makeGrid(rows), dictionary, 6)).toBe(true);
  });

  it("accepts five-letter lines formed by an outer block", () => {
    const rows = ["#ABCDE", "FGHIJK", "LMNOPQ", "RSTUVW", "XYZABC", "DEFGHI"];
    const dictionary = new Set<string>();
    for (const row of rows) dictionary.add(row.replace("#", ""));
    for (let c = 0; c < 6; c++) {
      dictionary.add(rows.map((row) => row[c]).join("").replace("#", ""));
    }
    expect(isWordSquare(6, makeGrid(rows), dictionary, 5)).toBe(true);
  });

  it("rejects an incomplete grid", () => {
    const grid = makeGrid(["SAD..S", "AGRAFE", "DRAFFS", "HAFFET", "EFFETE", "SESTET"]);
    expect(isWordSquare(6, grid, badDict, 6)).toBe(false);
  });

  it("rejects a grid with a bad row", () => {
    const grid = makeGrid(["XXXXXX", "AGRAFE", "DRAFFS", "HAFFET", "EFFETE", "SESTET"]);
    expect(isWordSquare(6, grid, badDict, 6)).toBe(false);
  });

  it("rejects a grid smaller than min length", () => {
    const grid = makeGrid(GOOD);
    expect(isWordSquare(6, grid, badDict, 7)).toBe(false);
  });

  it("accepts an alternative valid square that differs from the solution", () => {
    const solution = ["SADHES", "AGRAFE", "DRAFFS", "HAFFET", "EFFETE", "SESTET"];
    const alt = solution.map((row) => [...row].reverse().join(""));
    const dict = new Set<string>(solution);
    for (let c = 0; c < 6; c++) dict.add(solution.map((row) => row[c]).join(""));
    expect(alt.join("") !== solution.join("")).toBe(true);
    expect(isWordSquare(6, makeGrid(alt), dict, 6)).toBe(true);
  });

  it("flags only letters that differ from the solution", () => {
    const grid = makeGrid(["XADHES", "AGRAFE", "DRAFFS", "HAFFET", "EFFETE", "SESTET"]);
    const bad = incorrectCells(6, grid, GOOD);
    expect(bad.has("0-0")).toBe(true);
    expect(bad.has("0-1")).toBe(false);
    expect(bad.has("1-0")).toBe(false);
    expect(bad.has("1-1")).toBe(false);
  });

  it("does not flag empty boxes", () => {
    const grid = makeGrid(["XAD..S", "AGRAFE", ".RAFFS", "HAFFET", "EFFETE", "SESTET"]);
    const bad = incorrectCells(6, grid, GOOD);
    expect(bad.has("0-0")).toBe(true);
    expect(bad.has("0-3")).toBe(false);
    expect(bad.has("2-0")).toBe(false);
    expect(bad.size).toBe(1);
  });

  it("does not flag a correct grid", () => {
    const bad = incorrectCells(6, makeGrid(GOOD), GOOD);
    expect(bad.size).toBe(0);
  });

  it("reports completed valid rows and columns", () => {
    const rows = ["SADHES", "AGRAFE", "DRAFFS", "HAFFET", "EFFETE", "SESTET"];
    const dict = new Set<string>(rows);
    for (let c = 0; c < 6; c++) dict.add(rows.map((row) => row[c]).join(""));
    const { rows: validRows, cols: validCols } = validLines(6, makeGrid(rows), dict, 6);
    expect(validRows).toEqual(new Set([0, 1, 2, 3, 4, 5]));
    expect(validCols).toEqual(new Set([0, 1, 2, 3, 4, 5]));
  });

  it("reports valid backward-written words", () => {
    const rows = ["SECALP", "AGRAFE", "DRAFFS", "HAFFET", "EFFETE", "SESTET"];
    const dict = new Set(["PLACES", ...rows.slice(1)]);
    for (let c = 0; c < 6; c++) dict.add(rows.map((row) => row[c]).join(""));
    const { rows: validRows } = validLines(6, makeGrid(rows), dict, 6);
    expect(validRows.has(0)).toBe(true);
  });

  it("does not flag incomplete or invalid lines", () => {
    const rows = ["SAD..S", "AGRAFE", "DRAFFS", "HAFFET", "EFFETE", "SESTET"];
    const { rows: validRows, cols: validCols } = validLines(6, makeGrid(rows), badDict, 6);
    expect(validRows.has(0)).toBe(false);
    expect(validRows.has(1)).toBe(true);
    expect(validCols).toEqual(new Set([0, 1, 2, 5]));
  });

  it("handles five-letter lines formed by an outer block", () => {
    const rows = ["#ABCDE", "FGHIJK", "LMNOPQ", "RSTUVW", "XYZABC", "DEFGHI"];
    const dict = new Set<string>();
    for (const row of rows) dict.add(row.replace("#", ""));
    for (let c = 0; c < 6; c++) {
      dict.add(rows.map((row) => row[c]).join("").replace("#", ""));
    }
    const { rows: validRows, cols: validCols } = validLines(6, makeGrid(rows), dict, 5);
    expect(validRows.has(0)).toBe(true);
    expect(validCols.has(0)).toBe(true);
  });
});
