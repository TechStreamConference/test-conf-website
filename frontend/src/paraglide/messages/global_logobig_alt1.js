/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{}} Global_Logobig_Alt1Inputs */

const de_global_logobig_alt1 = /** @type {(inputs: Global_Logobig_Alt1Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Tech Stream Conference Logo`)
};

const en_global_logobig_alt1 = /** @type {(inputs: Global_Logobig_Alt1Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Tech Stream Conference Logo`)
};

/**
* | output |
* | --- |
* | "Tech Stream Conference Logo" |
*
* @param {Global_Logobig_Alt1Inputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
const global_logobig_alt1 = /** @type {((inputs?: Global_Logobig_Alt1Inputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Global_Logobig_Alt1Inputs, { locale?: "de" | "en" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_global_logobig_alt1(inputs)
	return en_global_logobig_alt1(inputs)
});
export { global_logobig_alt1 as "global_logoBig_alt" }