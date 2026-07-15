import { client } from '$gen/client.gen';
import { env } from '$env/dynamic/private';

const BACKEND_URL: string | undefined = env['FRONTEND_API_BASE_URL'];

if (!BACKEND_URL) {
	throw new Error('FRONTEND_API_BASE_URL is not configured');
}

client.setConfig({
	baseUrl: BACKEND_URL
});

export { client };
