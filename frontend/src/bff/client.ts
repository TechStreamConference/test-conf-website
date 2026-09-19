import { env } from '$env/dynamic/private';

import { client } from '$gen/client.gen';

const BACKEND_URL: string | undefined = env['BACKEND_ROOT_URI'];

if (!BACKEND_URL) {
    throw new Error('BACKEND_ROOT_URI is not configured');
}

client.setConfig({
    baseUrl: BACKEND_URL
});

export { client };
