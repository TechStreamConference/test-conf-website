// This prevents the newly opened page from being able to manipulate the original page through 'window.opener',
// which is both a security and performance improvement.
const NO_REFERRER: string = 'noopener noreferrer';

export enum LinkTarget {
	Self = '_self', // Open in the current tab (default).
	Blank = '_blank', // Open in a new tab/window.
	Parent = '_parent', // Open in the parent frame (rarely used).
	Top = '_top' // Open in the top-level frame (rarely used).
}

export function get_rel(target: LinkTarget): string | undefined {
	switch (target) {
		case LinkTarget.Blank:
			return NO_REFERRER;

		default:
			return undefined;
	}
}
