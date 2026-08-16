import type { Preview } from '@storybook/sveltekit';

import '../static/css/breakpoints.css';
import '../static/css/font.css';
import '../static/css/main.css';

const preview: Preview = {
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

export default preview;
