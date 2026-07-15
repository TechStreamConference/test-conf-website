import { client } from '$gen/client.gen';
import { env } from '$env/dynamic/private';

const BACKEND_URL: string = env.FRONTEND_API_BASE_URL;

client.setConfig({
	baseUrl: BACKEND_URL
});

export { client };
