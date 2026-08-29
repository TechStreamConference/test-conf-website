import { describe, expect, it, vi } from 'vitest';
import { isNumber, isUnsignedInt, unsignedIntOr } from '$lib/helper/numbers';

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

describe('unsignedIntOr', () => {
	it('should return the value unchanged when it is a valid unsigned int', () => {
		expect(unsignedIntOr(0, undefined)).toBe(0);
		expect(unsignedIntOr(42, undefined)).toBe(42);
	});

	it('should return undefined for undefined', () => {
		expect(unsignedIntOr(undefined, undefined)).toBeUndefined();
	});

	it('should return undefined for null', () => {
		expect(unsignedIntOr(null, undefined)).toBeUndefined();
	});

	it('should return undefined for a negative number', () => {
		expect(unsignedIntOr(-5, undefined)).toBeUndefined();
	});

	it('should return undefined for a non-integer number', () => {
		expect(unsignedIntOr(1.5, undefined)).toBeUndefined();
	});

	it('should return undefined for NaN', () => {
		expect(unsignedIntOr(NaN, undefined)).toBeUndefined();
	});

	it('should log a warning when rejecting an invalid unsigned int', () => {
		const logSpy = vi.spyOn(console, 'log').mockImplementation(() => undefined);
		unsignedIntOr(-5, undefined);
		expect(logSpy).toHaveBeenCalledOnce();
		logSpy.mockRestore();
	});

	it('should not log anything for undefined, null, or a valid value', () => {
		const logSpy = vi.spyOn(console, 'log').mockImplementation(() => undefined);
		unsignedIntOr(undefined, undefined);
		unsignedIntOr(null, undefined);
		unsignedIntOr(3, undefined);
		expect(logSpy).not.toHaveBeenCalled();
		logSpy.mockRestore();
	});
});
