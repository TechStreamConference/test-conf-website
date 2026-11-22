import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';

import { reroute } from '../hooks';

function routeArgument(pathname: string) {
    return { url: new URL(pathname, 'https://example.com'), fetch };
}

describe('reroute', () => {
    it('routes a language-prefixed path as the path without the prefix', () => {
        expect(reroute(routeArgument('/de/imprint'))).toBe('/imprint');
    });

    it('routes a bare language prefix as the root path', () => {
        expect(reroute(routeArgument('/de'))).toBe('/');
    });

    it('routes any ISO 639 code as a prefix, not only a supported UI language', () => {
        expect(reroute(routeArgument('/fr/imprint'))).toBe('/imprint');
    });

    it('leaves a path without a language prefix unchanged', () => {
        expect(reroute(routeArgument('/imprint'))).toBeUndefined();
        expect(reroute(routeArgument('/'))).toBeUndefined();
    });
});
