import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';

import { clampNumberToInt } from '$lib/helper/numbers';
import { isNumber } from '$lib/helper/numbers';
import { isUnsignedInt } from '$lib/helper/numbers';

describe('isNumber', () => {
    it('should be true for integers', () => {
        expect(isNumber(5)).toBe(true);
        expect(isNumber(-3)).toBe(true);
        expect(isNumber(0)).toBe(true);
    });

    it('should be true for floats', () => {
        expect(isNumber(1.5)).toBe(true);
    });

    it('should be true for NaN and Infinity, since they are still of type number', () => {
        expect(isNumber(NaN)).toBe(true);
        expect(isNumber(Infinity)).toBe(true);
        expect(isNumber(-Infinity)).toBe(true);
    });

    it('should be false for a numeric string', () => {
        expect(isNumber('5')).toBe(false);
    });

    it('should be false for null and undefined', () => {
        expect(isNumber(null)).toBe(false);
        expect(isNumber(undefined)).toBe(false);
    });

    it('should be false for booleans', () => {
        expect(isNumber(true)).toBe(false);
        expect(isNumber(false)).toBe(false);
    });

    it('should be false for objects and arrays', () => {
        expect(isNumber({})).toBe(false);
        expect(isNumber([1, 2, 3])).toBe(false);
    });

    it('should be false for a bigint', () => {
        expect(isNumber(5n)).toBe(false);
    });
});

describe('isUnsignedInt', () => {
    it('should be true for zero', () => {
        expect(isUnsignedInt(0)).toBe(true);
    });

    it('should be true for positive integers', () => {
        expect(isUnsignedInt(1)).toBe(true);
        expect(isUnsignedInt(1000)).toBe(true);
    });

    it('should be true for negative zero', () => {
        expect(isUnsignedInt(-0)).toBe(true);
    });

    it('should be false for negative integers', () => {
        expect(isUnsignedInt(-1)).toBe(false);
        expect(isUnsignedInt(-1000)).toBe(false);
    });

    it('should be false for non-integer numbers', () => {
        expect(isUnsignedInt(1.5)).toBe(false);
        expect(isUnsignedInt(-1.5)).toBe(false);
    });

    it('should be false for NaN', () => {
        expect(isUnsignedInt(NaN)).toBe(false);
    });

    it('should be false for Infinity', () => {
        expect(isUnsignedInt(Infinity)).toBe(false);
        expect(isUnsignedInt(-Infinity)).toBe(false);
    });
});

describe('clampNumberToInt', () => {
    it('should return an int when a float was provided', () => {
        expect(clampNumberToInt(1.3)).toBe(1);
        expect(clampNumberToInt(1.5)).toBe(2);
        expect(clampNumberToInt(1.6)).toBe(2);
        expect(clampNumberToInt(-1.2)).toBe(-1);
        expect(clampNumberToInt(-1.5)).toBe(-1);
        expect(clampNumberToInt(-1.8)).toBe(-2);
    });

    it('should return an int when an int was provided', () => {
        expect(clampNumberToInt(1)).toBe(1);
        expect(clampNumberToInt(-1)).toBe(-1);
    });

    it('should return a clamped int', () => {
        expect(clampNumberToInt(1, 10, 200)).toBe(10);
        expect(clampNumberToInt(300, 10, 200)).toBe(200);
    });

    it('should return zero for zero', () => {
        expect(clampNumberToInt(0)).toBe(0);
    });

    it('should round halves towards positive infinity', () => {
        expect(clampNumberToInt(0.5)).toBe(1);
        expect(clampNumberToInt(1.5)).toBe(2);
        expect(clampNumberToInt(2.5)).toBe(3);
        expect(clampNumberToInt(-1.5)).toBe(-1);
        expect(clampNumberToInt(-2.5)).toBe(-2);
    });

    it('should round to the nearest int just below and above a half', () => {
        expect(clampNumberToInt(2.4999)).toBe(2);
        expect(clampNumberToInt(2.5001)).toBe(3);
        expect(clampNumberToInt(-2.5001)).toBe(-3);
    });

    it('should return the value unchanged when it lies within the bounds', () => {
        expect(clampNumberToInt(50, 10, 200)).toBe(50);
        expect(clampNumberToInt(-50, -100, -10)).toBe(-50);
    });

    it('should return the bound when the value equals it', () => {
        expect(clampNumberToInt(10, 10, 200)).toBe(10);
        expect(clampNumberToInt(200, 10, 200)).toBe(200);
    });

    it('should clamp to the bounds when they are negative', () => {
        expect(clampNumberToInt(1, -5, -2)).toBe(-2);
        expect(clampNumberToInt(-9, -5, -2)).toBe(-5);
        expect(clampNumberToInt(-3, -5, -2)).toBe(-3);
    });

    it('should clamp to a range that contains zero', () => {
        expect(clampNumberToInt(-7, -5, 5)).toBe(-5);
        expect(clampNumberToInt(0, -5, 5)).toBe(0);
        expect(clampNumberToInt(7, -5, 5)).toBe(5);
    });

    it('should return the only possible value when min and max are equal', () => {
        expect(clampNumberToInt(5, 5, 5)).toBe(5);
        expect(clampNumberToInt(-100, 5, 5)).toBe(5);
        expect(clampNumberToInt(100, 5, 5)).toBe(5);
    });

    it('should round the value before it is clamped', () => {
        expect(clampNumberToInt(10.4, 0, 20)).toBe(10);
        expect(clampNumberToInt(19.6, 0, 20)).toBe(20);
        expect(clampNumberToInt(25.2, 0, 20)).toBe(20);
        expect(clampNumberToInt(-3.7, 0, 20)).toBe(0);
    });

    it('should use the default for the missing bound', () => {
        expect(clampNumberToInt(100, undefined, 50)).toBe(50);
        expect(clampNumberToInt(-100, undefined, 50)).toBe(-100);
        expect(clampNumberToInt(5, 10, undefined)).toBe(10);
        expect(clampNumberToInt(500, 10, undefined)).toBe(500);
    });

    it('should clamp infinite values to the safe integer range', () => {
        expect(clampNumberToInt(Infinity)).toBe(Number.MAX_SAFE_INTEGER);
        expect(clampNumberToInt(-Infinity)).toBe(Number.MIN_SAFE_INTEGER);
    });

    it('should clamp infinite values to the given bounds', () => {
        expect(clampNumberToInt(Infinity, 0, 100)).toBe(100);
        expect(clampNumberToInt(-Infinity, 0, 100)).toBe(0);
    });

    it('should clamp values outside the safe integer range', () => {
        expect(clampNumberToInt(1e20)).toBe(Number.MAX_SAFE_INTEGER);
        expect(clampNumberToInt(-1e20)).toBe(Number.MIN_SAFE_INTEGER);
        expect(clampNumberToInt(Number.MAX_SAFE_INTEGER + 2)).toBe(Number.MAX_SAFE_INTEGER);
    });

    it('should keep the safe integer limits themselves', () => {
        expect(clampNumberToInt(Number.MAX_SAFE_INTEGER)).toBe(Number.MAX_SAFE_INTEGER);
        expect(clampNumberToInt(Number.MIN_SAFE_INTEGER)).toBe(Number.MIN_SAFE_INTEGER);
    });

    it('should accept infinite bounds', () => {
        expect(clampNumberToInt(42, -Infinity, Infinity)).toBe(42);
    });

    it('should always return an integer for a finite value', () => {
        for (const value of [0.1, 0.9, 1e-9, 123.456, -123.456, 1e15 + 0.3]) {
            expect(Number.isInteger(clampNumberToInt(value))).toBe(true);
        }
    });
});
