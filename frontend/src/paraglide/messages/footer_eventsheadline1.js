/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{}} Footer_Eventsheadline1Inputs */

const de_footer_eventsheadline1 = /** @type {(inputs: Footer_Eventsheadline1Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Alle Events`)
};

const en_footer_eventsheadline1 = /** @type {(inputs: Footer_Eventsheadline1Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`All Events`)
};

/**
* | output |
* | --- |
* | "All Events" |
*
* @param {Footer_Eventsheadline1Inputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
const footer_eventsheadline1 = /** @type {((inputs?: Footer_Eventsheadline1Inputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Footer_Eventsheadline1Inputs, { locale?: "de" | "en" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_footer_eventsheadline1(inputs)
	return en_footer_eventsheadline1(inputs)
});
export { footer_eventsheadline1 as "footer_eventsHeadline" }