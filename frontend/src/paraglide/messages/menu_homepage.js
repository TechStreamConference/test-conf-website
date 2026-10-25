/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{}} Menu_HomepageInputs */

const de_menu_homepage = /** @type {(inputs: Menu_HomepageInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Startseite`)
};

const en_menu_homepage = /** @type {(inputs: Menu_HomepageInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Home`)
};

/**
* | output |
* | --- |
* | "Home" |
*
* @param {Menu_HomepageInputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
export const menu_homepage = /** @type {((inputs?: Menu_HomepageInputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Menu_HomepageInputs, { locale?: "de" | "en" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_menu_homepage(inputs)
	return en_menu_homepage(inputs)
});