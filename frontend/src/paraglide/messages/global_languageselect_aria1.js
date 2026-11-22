/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{}} Global_Languageselect_Aria1Inputs */

const de_global_languageselect_aria1 = /** @type {(inputs: Global_Languageselect_Aria1Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Sprachauswahl`)
};

const en_global_languageselect_aria1 = /** @type {(inputs: Global_Languageselect_Aria1Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Language selector`)
};

/**
* | output |
* | --- |
* | "Language selector" |
*
* @param {Global_Languageselect_Aria1Inputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
const global_languageselect_aria1 = /** @type {((inputs?: Global_Languageselect_Aria1Inputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Global_Languageselect_Aria1Inputs, { locale?: "de" | "en" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_global_languageselect_aria1(inputs)
	return en_global_languageselect_aria1(inputs)
});
export { global_languageselect_aria1 as "global_languageSelect_aria" }