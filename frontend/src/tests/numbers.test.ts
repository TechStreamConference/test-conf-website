import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';
import { vi } from 'vitest';

import { isNumber } from '$lib/helper/numbers';
import { isUnsignedInt } from '$lib/helper/numbers';
import { unsignedIntOr } from '$lib/helper/numbers';

import { validatorNotUnsignedInt } from '$logging/events.gen';
import { clientLogger } from '$logging/client';

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

const ORIGIN = 'test.origin';

describe('unsignedIntOr', () => {
    it('should return the value unchanged when it is a valid unsigned int', () => {
        expect(unsignedIntOr(0, ORIGIN)).toBe(0);
        expect(unsignedIntOr(42, ORIGIN)).toBe(42);
    });

    it('should return undefined for undefined', () => {
        expect(unsignedIntOr(undefined, ORIGIN)).toBeUndefined();
    });

    it('should return undefined for null', () => {
        expect(unsignedIntOr(null, ORIGIN)).toBeUndefined();
    });

    it('should return undefined for a negative number', () => {
        expect(unsignedIntOr(-5, ORIGIN)).toBeUndefined();
    });

    it('should return undefined for a non-integer number', () => {
        expect(unsignedIntOr(1.5, ORIGIN)).toBeUndefined();
    });

    it('should return undefined for NaN', () => {
        expect(unsignedIntOr(NaN, ORIGIN)).toBeUndefined();
    });

    it('should return the given default value instead of undefined', () => {
        expect(unsignedIntOr(undefined, ORIGIN, 10)).toBe(10);
        expect(unsignedIntOr(-5, ORIGIN, 10)).toBe(10);
    });

    it('should log a warning when rejecting an invalid unsigned int', () => {
        const logSpy = vi.spyOn(clientLogger, 'warning').mockImplementation(() => undefined);
        unsignedIntOr(-5, ORIGIN);
        expect(logSpy).toHaveBeenCalledOnce();
        expect(logSpy).toHaveBeenCalledWith(
            validatorNotUnsignedInt({ origin: ORIGIN, value: '-5' })
        );
        logSpy.mockRestore();
    });

    it.each([
        [-5, '-5'],
        [-0.5, '-0.5'],
        [1.5, '1.5'],
        [NaN, 'NaN'],
        [Infinity, 'Infinity'],
        [-Infinity, '-Infinity']
    ])('should log the value %s as the text %s', (value, text) => {
        const logSpy = vi.spyOn(clientLogger, 'warning').mockImplementation(() => undefined);
        unsignedIntOr(value, ORIGIN);
        expect(logSpy).toHaveBeenCalledWith(
            validatorNotUnsignedInt({ origin: ORIGIN, value: text })
        );
        logSpy.mockRestore();
    });

    it('should log the origin so the caller can be found', () => {
        const logSpy = vi.spyOn(clientLogger, 'warning').mockImplementation(() => undefined);
        unsignedIntOr(-1, 'input.Area.maxlength');
        expect(logSpy).toHaveBeenCalledWith(
            validatorNotUnsignedInt({
                origin: 'input.Area.maxlength',
                value: '-1'
            })
        );
        logSpy.mockRestore();
    });

    it('should log the default value that is used instead', () => {
        const logSpy = vi.spyOn(clientLogger, 'warning').mockImplementation(() => undefined);
        unsignedIntOr(-5, ORIGIN, 10);
        expect(logSpy).toHaveBeenCalledWith(
            validatorNotUnsignedInt({
                origin: ORIGIN,
                value: '-5',
                default_value: 10
            })
        );
        logSpy.mockRestore();
    });

    it('should not log anything for undefined, null, or a valid value', () => {
        const logSpy = vi.spyOn(clientLogger, 'warning').mockImplementation(() => undefined);
        unsignedIntOr(undefined, ORIGIN);
        unsignedIntOr(null, ORIGIN);
        unsignedIntOr(3, ORIGIN);
        expect(logSpy).not.toHaveBeenCalled();
        logSpy.mockRestore();
    });
});
