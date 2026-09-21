//
// Tech Stream Conference
// 2026
//
// Link targets and the matching rel attribute.
//

/**
 * @brief The targets a link can be opened in. The values are the native `target` attribute values.
 */
export enum LinkTarget {
    SameTab = '_self', // Open in the current tab (default).
    NewTab = '_blank', // Open in a new tab/window.
    Parent = '_parent', // Open in the parent frame (rarely used).
    Top = '_top' // Open in the top-level frame (rarely used).
}

// This prevents the newly opened page from being able to manipulate the original page through 'window.opener',
// which is both security and performance improvement.
const NO_REFERRER: string = 'noopener noreferrer';
export const DEFAULT_LINK_TARGET: LinkTarget = LinkTarget.NewTab;

/**
 * @brief Gets the rel attribute for a link.
 * @param target the link target
 * @param rels the other rel attributes
 * @returns the combined rel attributes
 */
export function getRel(target: LinkTarget, ...rels: (string | undefined | null)[]): string {
    const noReferrer = target === LinkTarget.NewTab ? NO_REFERRER : undefined;
    return [...rels, noReferrer].filter(Boolean).join(' ');
}
