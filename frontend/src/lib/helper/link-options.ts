export enum LinkTarget {
	SameTab = '_self', // Open in the current tab (default).
	NewTab = '_blank', // Open in a new tab/window.
	Parent = '_parent', // Open in the parent frame (rarely used).
	Top = '_top' // Open in the top-level frame (rarely used).
}

// This prevents the newly opened page from being able to manipulate the original page through 'window.opener',
// which is both a security and performance improvement.
const NO_REFERRER: string = 'noopener noreferrer';
export const DEFAULT_LINK_TARGET: LinkTarget = LinkTarget.NewTab;

export function get_rel(target: LinkTarget, ...rels: (string | undefined | null)[]): string {
	const no_referrer = target === LinkTarget.NewTab ? NO_REFERRER : undefined;
	return [...rels, no_referrer].filter(Boolean).join(' ');
}
