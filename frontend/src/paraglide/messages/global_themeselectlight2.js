/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{}} Global_Themeselectlight2Inputs */

const de_global_themeselectlight2 = /** @type {(inputs: Global_Themeselectlight2Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Hell`)
};

const en_global_themeselectlight2 = /** @type {(inputs: Global_Themeselectlight2Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Light`)
};

/**
* | output |
* | --- |
* | "Light" |
*
* @param {Global_Themeselectlight2Inputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
const global_themeselectlight2 = /** @type {((inputs?: Global_Themeselectlight2Inputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Global_Themeselectlight2Inputs, { locale?: "de" | "en" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_global_themeselectlight2(inputs)
	return en_global_themeselectlight2(inputs)
});
export { global_themeselectlight2 as "global_themeSelectLight" }