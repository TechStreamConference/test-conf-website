import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';
import { render } from 'vitest-browser-svelte';

import InputArea from '$lib/elements/input/Area.svelte';
import InputLine from '$lib/elements/input/Line.svelte';
import { InputType } from '$lib/helper/input';

const MAX_LENGTH = 10;

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
            .toHaveTextContent('Half of the character limit used, 5 characters remaining.');
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
            .toHaveTextContent('Character limit warning, 2 characters remaining.');
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
            .toHaveTextContent('Character limit critical, 1 characters remaining.');
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
            .toHaveTextContent('Half of the character limit used, 5 characters remaining.');
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
            .toHaveTextContent('Character limit warning, 2 characters remaining.');
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
            .toHaveTextContent('Character limit critical, 1 characters remaining.');
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
