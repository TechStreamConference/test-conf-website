import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';

import { RateLimiter } from '$logging/rate-limit';

const START = 1_000_000;

describe('RateLimiter', () => {
    it('should allow a burst up to the capacity', () => {
        const limiter = new RateLimiter(3, 1, START);
        expect(limiter.consume(START).allowed).toBe(true);
        expect(limiter.consume(START).allowed).toBe(true);
        expect(limiter.consume(START).allowed).toBe(true);
    });

    it('should reject the request after the capacity is used up', () => {
        const limiter = new RateLimiter(3, 1, START);
        for (let i = 0; i < 3; i++) {
            limiter.consume(START);
        }
        expect(limiter.consume(START).allowed).toBe(false);
        expect(limiter.consume(START).allowed).toBe(false);
    });

    it('should allow exactly one request with a capacity of one', () => {
        const limiter = new RateLimiter(1, 1, START);
        expect(limiter.consume(START).allowed).toBe(true);
        expect(limiter.consume(START).allowed).toBe(false);
    });

    it('should report no waiting time for an allowed request', () => {
        const limiter = new RateLimiter(1, 1, START);
        expect(limiter.consume(START)).toEqual({ allowed: true, retryAfterSeconds: 0 });
    });

    it('should report the time until the next token as the waiting time', () => {
        const limiter = new RateLimiter(1, 0.5, START);
        limiter.consume(START);
        expect(limiter.consume(START)).toEqual({ allowed: false, retryAfterSeconds: 2 });
    });

    it('should round the waiting time up to whole seconds', () => {
        const limiter = new RateLimiter(1, 1, START);
        limiter.consume(START);
        expect(limiter.consume(START + 400).retryAfterSeconds).toBe(1);
    });

    it('should not allow a request before a token has been refilled', () => {
        const limiter = new RateLimiter(1, 0.5, START);
        limiter.consume(START);
        expect(limiter.consume(START + 1999).allowed).toBe(false);
    });

    it('should allow a request again once a token has been refilled', () => {
        const limiter = new RateLimiter(1, 0.5, START);
        limiter.consume(START);
        expect(limiter.consume(START + 2000).allowed).toBe(true);
    });

    it('should keep a partial token between rejected requests', () => {
        const limiter = new RateLimiter(1, 1, START);
        limiter.consume(START);
        expect(limiter.consume(START + 500).allowed).toBe(false);
        expect(limiter.consume(START + 1000).allowed).toBe(true);
    });

    it('should refill according to the rate', () => {
        const limiter = new RateLimiter(10, 2, START);
        for (let i = 0; i < 10; i++) {
            limiter.consume(START);
        }
        // Two tokens per second, so two seconds bring back four requests.
        const results = Array.from({ length: 5 }, () => limiter.consume(START + 2000).allowed);
        expect(results).toEqual([true, true, true, true, false]);
    });

    it('should never refill above the capacity', () => {
        const limiter = new RateLimiter(2, 1, START);
        limiter.consume(START);
        limiter.consume(START);
        const later = START + 1_000_000;
        expect(limiter.consume(later).allowed).toBe(true);
        expect(limiter.consume(later).allowed).toBe(true);
        expect(limiter.consume(later).allowed).toBe(false);
    });

    it('should not remove tokens when the clock jumps backwards', () => {
        const limiter = new RateLimiter(2, 1, START);
        limiter.consume(START);
        expect(limiter.consume(START - 60_000).allowed).toBe(true);
        expect(limiter.consume(START - 60_000).allowed).toBe(false);
    });

    it('should continue to refill normally after the clock jumped backwards', () => {
        const limiter = new RateLimiter(1, 1, START);
        limiter.consume(START);
        expect(limiter.consume(START - 60_000).allowed).toBe(false);
        expect(limiter.consume(START - 59_000).allowed).toBe(true);
    });

    it('should support a rate below one request per second', () => {
        // 30 per minute, as it is configured with `LOG_BROWSER_RATE_LIMIT_PER_MINUTE`.
        const limiter = new RateLimiter(1, 30 / 60, START);
        limiter.consume(START);
        expect(limiter.consume(START + 1000).allowed).toBe(false);
        expect(limiter.consume(START + 2000).allowed).toBe(true);
    });

    it('should use the current time when none is given', () => {
        const limiter = new RateLimiter(1, 1);
        expect(limiter.consume().allowed).toBe(true);
        expect(limiter.consume().allowed).toBe(false);
    });
});
