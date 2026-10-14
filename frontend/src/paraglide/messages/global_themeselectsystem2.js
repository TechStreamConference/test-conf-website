/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{}} Global_Themeselectsystem2Inputs */

const de_global_themeselectsystem2 = /** @type {(inputs: Global_Themeselectsystem2Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`System`)
};

const en_global_themeselectsystem2 = /** @type {(inputs: Global_Themeselectsystem2Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`System`)
};

/**
* | output |
* | --- |
* | "System" |
*
* @param {Global_Themeselectsystem2Inputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
const global_themeselectsystem2 = /** @type {((inputs?: Global_Themeselectsystem2Inputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Global_Themeselectsystem2Inputs, { locale?: "de" | "en" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_global_themeselectsystem2(inputs)
	return en_global_themeselectsystem2(inputs)
});
export { global_themeselectsystem2 as "global_themeSelectSystem" }