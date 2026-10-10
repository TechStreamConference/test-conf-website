/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{}} Footer_Menuheadline1Inputs */

const de_footer_menuheadline1 = /** @type {(inputs: Footer_Menuheadline1Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Menü`)
};

const en_footer_menuheadline1 = /** @type {(inputs: Footer_Menuheadline1Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Menu`)
};

/**
* | output |
* | --- |
* | "Menu" |
*
* @param {Footer_Menuheadline1Inputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
const footer_menuheadline1 = /** @type {((inputs?: Footer_Menuheadline1Inputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Footer_Menuheadline1Inputs, { locale?: "de" | "en" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_footer_menuheadline1(inputs)
	return en_footer_menuheadline1(inputs)
});
export { footer_menuheadline1 as "footer_menuHeadline" }