/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{ year: NonNullable<unknown> }} Footer_CopyrightInputs */

const de_footer_copyright = /** @type {(inputs: Footer_CopyrightInputs) => LocalizedString} */ (i) => {
	return /** @type {LocalizedString} */ (`© Tech Stream Conference ${i?.year}`)
};

const en_footer_copyright = /** @type {(inputs: Footer_CopyrightInputs) => LocalizedString} */ (i) => {
	return /** @type {LocalizedString} */ (`© Tech Stream Conference ${i?.year}`)
};

/**
* | output |
* | --- |
* | "© Tech Stream Conference {year}" |
*
* @param {Footer_CopyrightInputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
export const footer_copyright = /** @type {((inputs: Footer_CopyrightInputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Footer_CopyrightInputs, { locale?: "de" | "en" }, {}>} */ ((inputs, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_footer_copyright(inputs)
	return en_footer_copyright(inputs)
});