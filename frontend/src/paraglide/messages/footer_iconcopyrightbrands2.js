/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{}} Footer_Iconcopyrightbrands2Inputs */

const de_footer_iconcopyrightbrands2 = /** @type {(inputs: Footer_Iconcopyrightbrands2Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Marken-Icons: Font Awesome Free von Fonticons, Inc., CC BY 4.0`)
};

const en_footer_iconcopyrightbrands2 = /** @type {(inputs: Footer_Iconcopyrightbrands2Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Brand icons: Font Awesome Free by Fonticons, Inc., CC BY 4.0`)
};

/**
* | output |
* | --- |
* | "Brand icons: Font Awesome Free by Fonticons, Inc., CC BY 4.0" |
*
* @param {Footer_Iconcopyrightbrands2Inputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
const footer_iconcopyrightbrands2 = /** @type {((inputs?: Footer_Iconcopyrightbrands2Inputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Footer_Iconcopyrightbrands2Inputs, { locale?: "de" | "en" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_footer_iconcopyrightbrands2(inputs)
	return en_footer_iconcopyrightbrands2(inputs)
});
export { footer_iconcopyrightbrands2 as "footer_iconCopyrightBrands" }