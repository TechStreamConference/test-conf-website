import type { Locale } from '$paraglide/runtime';

import { isLocale } from '$paraglide/runtime';

/**
 * @brief The placeholder values of a message by placeholder name.
 */
export type Inputs = Record<string, unknown>;

/**
 * @brief The placeholders of a message or menu that needs none.
 * A message without placeholders accepts any inputs, so it fits every menu.
 * A message that requires placeholders does not fit a menu without them.
 */
export type NoInputs = Inputs;

/**
 * @brief A message function as Paraglide generates it (e.g. `m.save`).
 * `TInputs` are the placeholder values the message needs.
 */
export type Message<TInputs> = (inputs: TInputs, options: { locale: Locale }) => string;

/**
 * @brief Prepares a language tag from the backend for Paraglide.
 * A tag with a region (`en-US`) is reduced to its language (`en`), unless the region itself is a supported language.
 * The result is not checked against the supported languages. Paraglide falls back to the base language for unknown ones.
 *
 * @param languageTag the language tag from the backend (case-insensitive)
 * @returns the lowercase language tag, without the region if the full tag is not supported
 */
export function normalizeLanguageTag(languageTag: string): string {
    const normalized = languageTag.toLowerCase();
    if (isLocale(normalized)) {
        return normalized;
    }

    return normalized.split('-')[0] ?? normalized;
}

/**
 * @brief Renders a message in the given language.
 *
 * @see normalizeLanguageTag
 *
 * @param message the message function from Paraglide (e.g. `m.save`)
 * @param languageTag the language tag from the backend
 * @param inputs the placeholder values of the message, only required if the message has placeholders
 * @returns the translated text
 */
export function i18n<TInputs extends Record<string, unknown>>(
    message: Message<TInputs>,
    languageTag: string,
    ...[inputs]: Record<string, never> extends TInputs ? [inputs?: TInputs] : [inputs: TInputs]
): string {
    // Paraglide types `locale` as the union of its languages, but falls back to the base language for any other value.
    return message((inputs ?? {}) as TInputs, {
        locale: normalizeLanguageTag(languageTag) as Locale
    });
}
