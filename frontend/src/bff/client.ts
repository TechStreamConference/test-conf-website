import { client } from '$gen/client.gen';

var BACKEND_URL: string = 'http://localhost/api'; // replace with docker variable

client.setConfig({
	baseUrl: BACKEND_URL,
})

export { client };
