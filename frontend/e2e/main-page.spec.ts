import { expect, test } from 'playwright/test';

test('main page contains the conference footer text', async ({ page }) => {
	await page.goto('/');

	await expect(page.locator('body')).toContainText(
		'TECH STREAM CONFERENCE – Online-Konferenz mit Vorträgen aus den Bereichen Programmierung, Maker-Szene und Spieleentwicklung'
	);
});
