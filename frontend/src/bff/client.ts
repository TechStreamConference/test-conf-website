// the client should only be imported from this file otherwise the config is missing.

import { client } from '$gen/client.gen';

client.setConfig({
	baseUrl: '/api'
});

export { client };
