/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{}} Extra_KeyInputs */

const de_extra_key = /** @type {(inputs: Extra_KeyInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`extra_key`)
};

const en_extra_key = /** @type {(inputs: Extra_KeyInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`extra_key`)
};

/**
* | output |
* | --- |
* | "extra_key" |
*
* @param {Extra_KeyInputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
export const extra_key = /** @type {((inputs?: Extra_KeyInputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Extra_KeyInputs, { locale?: "de" | "en" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_extra_key(inputs)
	return en_extra_key(inputs)
});