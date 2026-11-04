/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{}} Footer_Iconcopyrightgeneral2Inputs */

const de_footer_iconcopyrightgeneral2 = /** @type {(inputs: Footer_Iconcopyrightgeneral2Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Weitere Icons: Font Awesome Free von Fonticons, Inc., CC BY 4.0`)
};

const en_footer_iconcopyrightgeneral2 = /** @type {(inputs: Footer_Iconcopyrightgeneral2Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Other icons: Font Awesome Free by Fonticons, Inc., CC BY 4.0`)
};

/**
* | output |
* | --- |
* | "Other icons: Font Awesome Free by Fonticons, Inc., CC BY 4.0" |
*
* @param {Footer_Iconcopyrightgeneral2Inputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
const footer_iconcopyrightgeneral2 = /** @type {((inputs?: Footer_Iconcopyrightgeneral2Inputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Footer_Iconcopyrightgeneral2Inputs, { locale?: "de" | "en" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_footer_iconcopyrightgeneral2(inputs)
	return en_footer_iconcopyrightgeneral2(inputs)
});
export { footer_iconcopyrightgeneral2 as "footer_iconCopyrightGeneral" }