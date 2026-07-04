import { describe, expect, it } from 'vitest';

// There needs to be at least one test otherwise vitetest fails.
// So this test will be sitting here for just not having this false negative.
describe('Sample test', () => {
	it('should pass', () => {
		expect(1 + 1).toBe(2);
	});
});
