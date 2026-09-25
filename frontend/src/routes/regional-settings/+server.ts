import { json } from '@sveltejs/kit';

import { getCurrentUser } from '$bff/v1/auth.server';
import { reportRegionalSettings } from '$bff/v1/users.server';
import type { ReportedRegionalSettingsInputV1 } from '$gen/types.gen';

import type { RequestHandler } from './$types';

export const GET: RequestHandler = async (event) => {
	const result = await getCurrentUser(event);
	if (!result.ok) {
		return new Response(null, { status: result.status });
	}
	return json(result.data);
};

export const PUT: RequestHandler = async (event) => {
	const body = (await event.request.json()) as ReportedRegionalSettingsInputV1;
	const result = await reportRegionalSettings(event, body);
	if (!result.ok) {
		return new Response(null, { status: result.status });
	}
	return new Response(null, { status: 204 });
};
