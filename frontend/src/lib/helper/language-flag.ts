// A language tag has no inherent flag (e.g. several countries speak French), so a region is picked for every
// language tag that does not already carry one itself (e.g. `de-AT`).
const LANGUAGE_REGION_OVERRIDES: Record<string, string> = {
    en: 'GB'
};

/**
 * @brief Derives the `flag-icons` country code for a language tag.
 * @param languageTag the language tag, e.g. `de` or `de-AT`.
 * @returns the lowercase ISO 3166-1 alpha-2 country code, e.g. `de` or `at`.
 */
export function languageTagToFlagCountryCode(languageTag: string): string {
    const locale = new Intl.Locale(languageTag);
    const region = locale.region ?? LANGUAGE_REGION_OVERRIDES[locale.language] ?? locale.language;
    return region.toLowerCase();
}

/**
 * @brief The native name of a language, e.g. `Deutsch` for `de`.
 * @param languageTag the language tag.
 * @returns the native name of the language, or the tag itself if it cannot be resolved.
 */
export function nativeLanguageName(languageTag: string): string {
    return (
        new Intl.DisplayNames([languageTag], { type: 'language' }).of(languageTag) ?? languageTag
    );
}
