/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{}} Global_Themeselect_Aria1Inputs */

const de_global_themeselect_aria1 = /** @type {(inputs: Global_Themeselect_Aria1Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Farbschema-Auswahl`)
};

const en_global_themeselect_aria1 = /** @type {(inputs: Global_Themeselect_Aria1Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Theme selector`)
};

/**
* | output |
* | --- |
* | "Theme selector" |
*
* @param {Global_Themeselect_Aria1Inputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
const global_themeselect_aria1 = /** @type {((inputs?: Global_Themeselect_Aria1Inputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Global_Themeselect_Aria1Inputs, { locale?: "de" | "en" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_global_themeselect_aria1(inputs)
	return en_global_themeselect_aria1(inputs)
});
export { global_themeselect_aria1 as "global_themeSelect_aria" }