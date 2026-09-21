//
// Tech Stream Conference
// 2026
//
// Storybook preview configuration and global CSS imports.
//

import type { Preview } from '@storybook/sveltekit';

import '../static/css/breakpoints.css';
import '../static/css/font.css';
import '../static/css/main.css';
import './preview.css';

const PREVIEW: Preview = {
    parameters: {
        controls: {
            matchers: {
                color: /(background|color)$/i,
                date: /Date$/i
            }
        },
        layout: 'centered'
    }
};

export default PREVIEW;
