import type { MockInstance } from 'vitest';
import { afterEach } from 'vitest';
import { beforeEach } from 'vitest';
import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';
import { vi } from 'vitest';

const mocks = vi.hoisted(() => {
    const env: Record<string, string | undefined> = {};
    return { env };
});

vi.mock('$env/dynamic/private', () => ({ env: mocks.env }));

import type * as LoggerModule from '$logging';
import { validatorNotUnsignedInt } from '$logging/events.gen';

const EVENT = validatorNotUnsignedInt({ origin: 'test.origin', value: '-3' });

/**
 * @brief Loads the logger anew, because it reads the environment when it is loaded.
 * @returns the module of the logger.
 */
async function loadLogger(): Promise<typeof LoggerModule> {
    vi.resetModules();
    return await import('$logging');
}

/**
 * @brief Parses the JSON line the logger wrote to `stdout`.
 * @param write the spy on `process.stdout.write`.
 * @returns the record.
 */
function writtenRecord(write: MockInstance<typeof process.stdout.write>): Record<string, unknown> {
    expect(write).toHaveBeenCalledOnce();
    return JSON.parse(String(write.mock.calls[0]?.[0])) as Record<string, unknown>;
}

beforeEach(() => {
    delete mocks.env['LOG_FILE'];
    delete mocks.env['ENVIRONMENT'];
});

afterEach(() => {
    vi.restoreAllMocks();
});

describe('logger', () => {
    it('should mark records of the logger with the source bff', async () => {
        const write = vi.spyOn(process.stdout, 'write').mockImplementation(() => true);
        const { logger } = await loadLogger();
        logger.warning(EVENT);
        expect(writtenRecord(write)['source']).toBe('bff');
    });

    it('should mark records of the browser logger with the source browser', async () => {
        const write = vi.spyOn(process.stdout, 'write').mockImplementation(() => true);
        const { browserLogger } = await loadLogger();
        browserLogger.warning(EVENT);
        expect(writtenRecord(write)['source']).toBe('browser');
    });

    it('should write the page when it is given', async () => {
        const write = vi.spyOn(process.stdout, 'write').mockImplementation(() => true);
        const { browserLogger } = await loadLogger();
        browserLogger.warning(EVENT, { page: '/login' });
        expect(writtenRecord(write)['page']).toBe('/login');
    });

    it('should leave out the page when none is given', async () => {
        const write = vi.spyOn(process.stdout, 'write').mockImplementation(() => true);
        const { logger } = await loadLogger();
        logger.warning(EVENT);
        expect(writtenRecord(write)).not.toHaveProperty('page');
    });

    it('should leave out the page when the context has none', async () => {
        const write = vi.spyOn(process.stdout, 'write').mockImplementation(() => true);
        const { logger } = await loadLogger();
        logger.warning(EVENT, {});
        expect(writtenRecord(write)).not.toHaveProperty('page');
    });

    it('should not let the page overwrite the source', async () => {
        const write = vi.spyOn(process.stdout, 'write').mockImplementation(() => true);
        const { browserLogger } = await loadLogger();
        browserLogger.warning(EVENT, { page: '/login' });
        expect(writtenRecord(write)['source']).toBe('browser');
    });
});
