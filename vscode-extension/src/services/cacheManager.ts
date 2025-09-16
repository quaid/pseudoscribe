import * as vscode from 'vscode';

/**
 * Cache manager for offline capability and performance optimization
 * Implements BDD scenario: "Offline capability for basic features"
 */
export class CacheManager {
    private context: vscode.ExtensionContext;
    private readonly CACHE_PREFIX = 'pseudoscribe_cache_';
    private readonly DEFAULT_TTL = 300000; // 5 minutes in milliseconds

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    /**
     * Store data in cache with TTL
     * BDD: When backend API is unavailable, cached data should be available
     */
    async set(key: string, data: any, ttl: number = this.DEFAULT_TTL): Promise<void> {
        const cacheEntry = {
            data: data,
            timestamp: Date.now(),
            ttl: ttl
        };

        const cacheKey = this.CACHE_PREFIX + key;
        await this.context.globalState.update(cacheKey, cacheEntry);
    }

    /**
     * Retrieve data from cache if not expired
     * BDD: Basic style checking should work with local rules when offline
     */
    async get(key: string): Promise<any | null> {
        const cacheKey = this.CACHE_PREFIX + key;
        const cacheEntry = this.context.globalState.get(cacheKey) as any;

        if (!cacheEntry) {
            return null;
        }

        // Check if cache entry has expired
        const now = Date.now();
        if (now - cacheEntry.timestamp > cacheEntry.ttl) {
            // Remove expired entry
            await this.context.globalState.update(cacheKey, undefined);
            return null;
        }

        return cacheEntry.data;
    }

    /**
     * Check if data exists in cache and is not expired
     */
    async has(key: string): Promise<boolean> {
        const data = await this.get(key);
        return data !== null;
    }

    /**
     * Remove specific cache entry
     */
    async remove(key: string): Promise<void> {
        const cacheKey = this.CACHE_PREFIX + key;
        await this.context.globalState.update(cacheKey, undefined);
    }

    /**
     * Clear all cache entries
     */
    async clear(): Promise<void> {
        const keys = this.context.globalState.keys();
        const cacheKeys = keys.filter(key => key.startsWith(this.CACHE_PREFIX));
        
        for (const key of cacheKeys) {
            await this.context.globalState.update(key, undefined);
        }
    }

    /**
     * Get cache statistics
     */
    async getStats(): Promise<{totalEntries: number, totalSize: number}> {
        const keys = this.context.globalState.keys();
        const cacheKeys = keys.filter(key => key.startsWith(this.CACHE_PREFIX));
        
        let totalSize = 0;
        for (const key of cacheKeys) {
            const entry = this.context.globalState.get(key);
            if (entry) {
                totalSize += JSON.stringify(entry).length;
            }
        }

        return {
            totalEntries: cacheKeys.length,
            totalSize: totalSize
        };
    }

    /**
     * Clean up expired cache entries
     */
    async cleanup(): Promise<number> {
        const keys = this.context.globalState.keys();
        const cacheKeys = keys.filter(key => key.startsWith(this.CACHE_PREFIX));
        let removedCount = 0;

        const now = Date.now();
        for (const key of cacheKeys) {
            const entry = this.context.globalState.get(key) as any;
            if (entry && (now - entry.timestamp > entry.ttl)) {
                await this.context.globalState.update(key, undefined);
                removedCount++;
            }
        }

        return removedCount;
    }
}
