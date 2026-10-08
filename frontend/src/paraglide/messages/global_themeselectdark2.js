/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{}} Global_Themeselectdark2Inputs */

const de_global_themeselectdark2 = /** @type {(inputs: Global_Themeselectdark2Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Dunkel`)
};

const en_global_themeselectdark2 = /** @type {(inputs: Global_Themeselectdark2Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Dark`)
};

/**
* | output |
* | --- |
* | "Dark" |
*
* @param {Global_Themeselectdark2Inputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
const global_themeselectdark2 = /** @type {((inputs?: Global_Themeselectdark2Inputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Global_Themeselectdark2Inputs, { locale?: "de" | "en" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_global_themeselectdark2(inputs)
	return en_global_themeselectdark2(inputs)
});
export { global_themeselectdark2 as "global_themeSelectDark" }