import { expect } from 'playwright/test';
import { test } from 'playwright/test';

test.describe('with an English browser', () => {
    test.use({ locale: 'en-US' });

    test('main page contains the English conference footer text', async ({ page }) => {
        await page.goto('/');

        await expect(page.locator('body')).toContainText(
            'TECH STREAM CONFERENCE – Online conference with talks on programming, the maker scene and game development'
        );
    });
});

test.describe('with a German browser', () => {
    test.use({ locale: 'de-DE' });

    test('main page contains the German conference footer text', async ({ page }) => {
        await page.goto('/');

        await expect(page.locator('body')).toContainText(
            'TECH STREAM CONFERENCE – Online-Konferenz mit Vorträgen aus den Bereichen Programmierung, Maker-Szene und Spieleentwicklung'
        );
    });
});
