import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';
import { tick } from 'svelte';
import { userEvent } from 'vitest/browser';
import { render } from 'vitest-browser-svelte';

import InputArea from '$lib/elements/input/Area.svelte';
import InputLine from '$lib/elements/input/Line.svelte';
import { InputType } from '$lib/helper/input';

const MAX_LENGTH = 10;

// With MAX_LENGTH = 10 the severity changes at these lengths: half, warning, critical, reached.
const FULL_TEXT = '1234567890';
const SEVERITY_CHANGE_COUNT = 4;

type CounterKind = 'line' | 'area';
const COUNTER_KINDS: CounterKind[] = ['line', 'area'];

async function renderCounter(kind: CounterKind, value: string = '') {
    if (kind === 'line') {
        return await render(InputLine, {
            id: 'input-line',
            label: 'Title',
            type: InputType.Text,
            maxlength: MAX_LENGTH,
            value
        });
    }
    return await render(InputArea, {
        id: 'input-area',
        label: 'Description',
        maxlength: MAX_LENGTH,
        value
    });
}

function labelOf(kind: CounterKind): string {
    return kind === 'line' ? 'Title' : 'Description';
}

/**
 * @brief Counts how often the content of the given live region changes.
 *
 * A screen reader announces a live region only when its content changes, so the number of DOM
 * mutations equals the number of possible announcements.
 *
 * @param status the live region to observe.
 * @returns a function that returns the number of mutations observed so far.
 */
function countMutations(status: HTMLElement): () => number {
    const records: MutationRecord[] = [];
    const observer = new MutationObserver((mutations) => records.push(...mutations));
    observer.observe(status, { characterData: true, childList: true, subtree: true });

    return () => {
        // Pending records are not delivered to the callback yet.
        records.push(...observer.takeRecords());
        return records.length;
    };
}

async function pressKeys(keys: string, times: number = 1) {
    for (let i = 0; i < times; ++i) {
        await userEvent.keyboard(keys);
        await tick();
    }
}

describe('character limit announcement text', () => {
    it('has no announcement while the value is below the half threshold (InputLine)', async () => {
        const screen = await render(InputLine, {
            id: 'input-line',
            label: 'Title',
            type: InputType.Text,
            maxlength: MAX_LENGTH,
            value: ''
        });

        await screen.getByLabelText('Title').fill('1234');

        await expect.element(screen.getByRole('status')).toHaveTextContent('');
    });

    it('has no announcement while the value is below the half threshold (InputArea)', async () => {
        const screen = await render(InputArea, {
            id: 'input-area',
            label: 'Description',
            maxlength: MAX_LENGTH,
            value: ''
        });

        await screen.getByLabelText('Description').fill('1234');

        await expect.element(screen.getByRole('status')).toHaveTextContent('');
    });

    it('announces the half message once half of the max length is used (InputLine)', async () => {
        const screen = await render(InputLine, {
            id: 'input-line',
            label: 'Title',
            type: InputType.Text,
            maxlength: MAX_LENGTH,
            value: ''
        });

        await screen.getByLabelText('Title').fill('12345');

        await expect
            .element(screen.getByRole('status'))
            .toHaveTextContent('Half of the character limit used.');
    });

    it('announces the warning message once the warning threshold is crossed (InputLine)', async () => {
        const screen = await render(InputLine, {
            id: 'input-line',
            label: 'Title',
            type: InputType.Text,
            maxlength: MAX_LENGTH,
            value: ''
        });

        await screen.getByLabelText('Title').fill('12345678');

        await expect
            .element(screen.getByRole('status'))
            .toHaveTextContent('Character limit warning.');
    });

    it('announces the critical message once the critical threshold is crossed (InputLine)', async () => {
        const screen = await render(InputLine, {
            id: 'input-line',
            label: 'Title',
            type: InputType.Text,
            maxlength: MAX_LENGTH,
            value: ''
        });

        await screen.getByLabelText('Title').fill('123456789');

        await expect
            .element(screen.getByRole('status'))
            .toHaveTextContent('Character limit critical.');
    });

    it('announces the limit-reached message once the max length is reached (InputLine)', async () => {
        const screen = await render(InputLine, {
            id: 'input-line',
            label: 'Title',
            type: InputType.Text,
            maxlength: MAX_LENGTH,
            value: ''
        });

        await screen.getByLabelText('Title').fill('1234567890');

        await expect
            .element(screen.getByRole('status'))
            .toHaveTextContent('Character limit reached.');
    });

    it('announces the half message once half of the max length is used (InputArea)', async () => {
        const screen = await render(InputArea, {
            id: 'input-area',
            label: 'Description',
            maxlength: MAX_LENGTH,
            value: ''
        });

        await screen.getByLabelText('Description').fill('12345');

        await expect
            .element(screen.getByRole('status'))
            .toHaveTextContent('Half of the character limit used.');
    });

    it('announces the warning message once the warning threshold is crossed (InputArea)', async () => {
        const screen = await render(InputArea, {
            id: 'input-area',
            label: 'Description',
            maxlength: MAX_LENGTH,
            value: ''
        });

        await screen.getByLabelText('Description').fill('12345678');

        await expect
            .element(screen.getByRole('status'))
            .toHaveTextContent('Character limit warning.');
    });

    it('announces the critical message once the critical threshold is crossed (InputArea)', async () => {
        const screen = await render(InputArea, {
            id: 'input-area',
            label: 'Description',
            maxlength: MAX_LENGTH,
            value: ''
        });

        await screen.getByLabelText('Description').fill('123456789');

        await expect
            .element(screen.getByRole('status'))
            .toHaveTextContent('Character limit critical.');
    });

    it('announces the limit-reached message once the max length is reached (InputArea)', async () => {
        const screen = await render(InputArea, {
            id: 'input-area',
            label: 'Description',
            maxlength: MAX_LENGTH,
            value: ''
        });

        await screen.getByLabelText('Description').fill('1234567890');

        await expect
            .element(screen.getByRole('status'))
            .toHaveTextContent('Character limit reached.');
    });
});

describe('character limit announcement DOM attributes', () => {
    it('exposes the announcement element as a polite, atomic status region (InputLine)', async () => {
        const screen = await render(InputLine, {
            id: 'input-line',
            label: 'Title',
            type: InputType.Text,
            maxlength: MAX_LENGTH,
            value: ''
        });

        const status = screen.getByRole('status');

        await expect.element(status).toHaveAttribute('aria-atomic', 'true');
    });

    it('exposes the announcement element as a polite, atomic status region (InputArea)', async () => {
        const screen = await render(InputArea, {
            id: 'input-area',
            label: 'Description',
            maxlength: MAX_LENGTH,
            value: ''
        });

        const status = screen.getByRole('status');

        await expect.element(status).toHaveAttribute('aria-atomic', 'true');
    });
});

describe.each(COUNTER_KINDS)('character limit announcement frequency (%s)', (kind) => {
    it('changes the announcement only when a severity threshold is crossed while typing', async () => {
        const screen = await renderCounter(kind);
        const input = screen.getByLabelText(labelOf(kind));
        const status = screen.getByRole('status').element() as HTMLElement;
        const mutationCount = countMutations(status);

        await input.click();
        await pressKeys('a', FULL_TEXT.length);

        expect(mutationCount()).toBe(SEVERITY_CHANGE_COUNT);
    });

    it('does not change the announcement while the severity stays the same', async () => {
        const screen = await renderCounter(kind, '12345');
        const input = screen.getByLabelText(labelOf(kind));
        const status = screen.getByRole('status').element() as HTMLElement;
        await expect
            .element(screen.getByRole('status'))
            .toHaveTextContent('Half of the character limit used.');
        const mutationCount = countMutations(status);

        await input.click();
        await userEvent.keyboard('{End}');
        await pressKeys('a', 2);

        expect(mutationCount()).toBe(0);
        await expect
            .element(screen.getByRole('status'))
            .toHaveTextContent('Half of the character limit used.');
    });

    it('changes the announcement only when a severity threshold is crossed while deleting', async () => {
        const screen = await renderCounter(kind, FULL_TEXT);
        const input = screen.getByLabelText(labelOf(kind));
        const status = screen.getByRole('status').element() as HTMLElement;
        await expect
            .element(screen.getByRole('status'))
            .toHaveTextContent('Character limit reached.');
        const mutationCount = countMutations(status);

        await input.click();
        await userEvent.keyboard('{End}');
        await pressKeys('{Backspace}', FULL_TEXT.length);

        // Critical, warning and half are entered while deleting, then the announcement is cleared.
        expect(mutationCount()).toBe(SEVERITY_CHANGE_COUNT);
        expect(status.textContent).toBe('');
    });
});
