import { describe, expect, it, vi } from 'vitest';
import { is_number, is_valid_unsigned_int, validate_unsigned_int } from '$lib/helper/numbers';

describe('is_number', () => {
	it('should be true for integers', () => {
		expect(is_number(5)).toBe(true);
		expect(is_number(-3)).toBe(true);
		expect(is_number(0)).toBe(true);
	});

	it('should be true for floats', () => {
		expect(is_number(1.5)).toBe(true);
	});

	it('should be true for NaN and Infinity, since they are still of type number', () => {
		expect(is_number(NaN)).toBe(true);
		expect(is_number(Infinity)).toBe(true);
		expect(is_number(-Infinity)).toBe(true);
	});

	it('should be false for a numeric string', () => {
		expect(is_number('5')).toBe(false);
	});

	it('should be false for null and undefined', () => {
		expect(is_number(null)).toBe(false);
		expect(is_number(undefined)).toBe(false);
	});

	it('should be false for booleans', () => {
		expect(is_number(true)).toBe(false);
		expect(is_number(false)).toBe(false);
	});

	it('should be false for objects and arrays', () => {
		expect(is_number({})).toBe(false);
		expect(is_number([1, 2, 3])).toBe(false);
	});

	it('should be false for a bigint', () => {
		expect(is_number(5n)).toBe(false);
	});
});

describe('is_valid_unsigned_int', () => {
	it('should be true for zero', () => {
		expect(is_valid_unsigned_int(0)).toBe(true);
	});

	it('should be true for positive integers', () => {
		expect(is_valid_unsigned_int(1)).toBe(true);
		expect(is_valid_unsigned_int(1000)).toBe(true);
	});

	it('should be true for negative zero', () => {
		expect(is_valid_unsigned_int(-0)).toBe(true);
	});

	it('should be false for negative integers', () => {
		expect(is_valid_unsigned_int(-1)).toBe(false);
		expect(is_valid_unsigned_int(-1000)).toBe(false);
	});

	it('should be false for non-integer numbers', () => {
		expect(is_valid_unsigned_int(1.5)).toBe(false);
		expect(is_valid_unsigned_int(-1.5)).toBe(false);
	});

	it('should be false for NaN', () => {
		expect(is_valid_unsigned_int(NaN)).toBe(false);
	});

	it('should be false for Infinity', () => {
		expect(is_valid_unsigned_int(Infinity)).toBe(false);
		expect(is_valid_unsigned_int(-Infinity)).toBe(false);
	});
});

describe('validate_unsigned_int', () => {
	it('should return the value unchanged when it is a valid unsigned int', () => {
		expect(validate_unsigned_int(0)).toBe(0);
		expect(validate_unsigned_int(42)).toBe(42);
	});

	it('should return undefined for undefined', () => {
		expect(validate_unsigned_int(undefined)).toBeUndefined();
	});

	it('should return undefined for null', () => {
		expect(validate_unsigned_int(null)).toBeUndefined();
	});

	it('should return undefined for a negative number', () => {
		expect(validate_unsigned_int(-5)).toBeUndefined();
	});

	it('should return undefined for a non-integer number', () => {
		expect(validate_unsigned_int(1.5)).toBeUndefined();
	});

	it('should return undefined for NaN', () => {
		expect(validate_unsigned_int(NaN)).toBeUndefined();
	});

	it('should return undefined for a value that is not actually a number at runtime', () => {
		expect(validate_unsigned_int('5' as unknown as number)).toBeUndefined();
	});

	it('should log a warning when rejecting an invalid unsigned int', () => {
		const logSpy = vi.spyOn(console, 'log').mockImplementation(() => undefined);
		validate_unsigned_int(-5);
		expect(logSpy).toHaveBeenCalledOnce();
		logSpy.mockRestore();
	});

	it('should not log anything for undefined, null, or a valid value', () => {
		const logSpy = vi.spyOn(console, 'log').mockImplementation(() => undefined);
		validate_unsigned_int(undefined);
		validate_unsigned_int(null);
		validate_unsigned_int(3);
		expect(logSpy).not.toHaveBeenCalled();
		logSpy.mockRestore();
	});
});
