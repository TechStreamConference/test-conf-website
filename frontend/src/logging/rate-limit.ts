/**
 * @brief The outcome of a rate limit check.
 */
export interface RateLimitResult {
    allowed: boolean;
    retryAfterSeconds: number;
}

/**
 * @brief An in-memory token bucket rate limiter.
 * Every request costs one token. Tokens are added back over time, up to the capacity.
 * The state lives in the memory of the current process. It is not shared between instances and is lost on restart.
 */
export class RateLimiter {
    private tokens: number;
    private updatedAt: number;

    /**
     * @param capacity the number of requests that are allowed in a burst.
     * @param refillPerSecond how many requests are added back per second.
     * @param now the current time in milliseconds, the bucket starts full at this time.
     */
    constructor(
        private readonly capacity: number,
        private readonly refillPerSecond: number,
        now: number = Date.now()
    ) {
        this.tokens = capacity;
        this.updatedAt = now;
    }

    /**
     * @brief Consumes one request, if there is one left.
     * @param now the current time in milliseconds.
     * @returns whether the request is allowed and, if not, how many seconds to wait.
     */
    consume(now: number = Date.now()): RateLimitResult {
        // The clock may jump backwards, e.g. when it is adjusted. That must never remove tokens.
        const elapsedSeconds = Math.max(0, now - this.updatedAt) / 1000;
        this.tokens = Math.min(this.capacity, this.tokens + elapsedSeconds * this.refillPerSecond);
        this.updatedAt = now;

        if (this.tokens >= 1) {
            this.tokens -= 1;
            return { allowed: true, retryAfterSeconds: 0 };
        }
        return {
            allowed: false,
            retryAfterSeconds: Math.ceil((1 - this.tokens) / this.refillPerSecond)
        };
    }
}
