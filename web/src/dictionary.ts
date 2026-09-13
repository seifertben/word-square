// Client dictionary loader: fetches the trimmed word list once and makes a Set.

let cache: Set<string> | null = null;
let pending: Promise<Set<string>> | null = null;

export async function loadDictionary(): Promise<Set<string>> {
  if (cache) return cache;
  if (!pending) {
    pending = fetch(`${import.meta.env.BASE_URL}dictionary/words.json`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load dictionary (${res.status})`);
        return res.json() as Promise<string[]>;
      })
      .then((words) => new Set(words));
  }
  cache = await pending;
  return cache;
}

/** Test hook: inject a dictionary without network (used by vitest). */
export function setDictionary(words: Set<string>): void {
  cache = words;
  pending = null;
}
