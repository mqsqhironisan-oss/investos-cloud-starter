type CacheBinding = KVNamespace | undefined;

class MemoryCache {
  private store = new Map<string, { value: string; expiresAt?: number }>();

  async get(key: string): Promise<string | null> {
    const hit = this.store.get(key);
    if (!hit) return null;
    if (hit.expiresAt && hit.expiresAt < Date.now()) {
      this.store.delete(key);
      return null;
    }
    return hit.value;
  }

  async put(key: string, value: string, options?: { expirationTtl?: number }) {
    const expiresAt = options?.expirationTtl
      ? Date.now() + options.expirationTtl * 1000
      : undefined;
    this.store.set(key, { value, expiresAt });
  }
}

const fallback = new MemoryCache();

export function getCache(env: { CACHE?: CacheBinding } | Record<string, unknown>): CacheBinding | MemoryCache {
  return (env as { CACHE?: CacheBinding }).CACHE ?? fallback;
}

export async function readThrough<T>(
  cache: CacheBinding | MemoryCache,
  key: string,
  factory: () => Promise<T>,
  ttlSeconds = 300
): Promise<T> {
  const cached = await (cache as any).get(key);
  if (cached) return JSON.parse(cached) as T;
  const value = await factory();
  await (cache as any).put(key, JSON.stringify(value), { expirationTtl: ttlSeconds });
  return value;
}
