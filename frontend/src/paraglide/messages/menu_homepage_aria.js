/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{}} Menu_Homepage_AriaInputs */

const de_menu_homepage_aria = /** @type {(inputs: Menu_Homepage_AriaInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Zur Startseite`)
};

const en_menu_homepage_aria = /** @type {(inputs: Menu_Homepage_AriaInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Go to the homepage`)
};

/**
* | output |
* | --- |
* | "Go to the homepage" |
*
* @param {Menu_Homepage_AriaInputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
export const menu_homepage_aria = /** @type {((inputs?: Menu_Homepage_AriaInputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Menu_Homepage_AriaInputs, { locale?: "de" | "en" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_menu_homepage_aria(inputs)
	return en_menu_homepage_aria(inputs)
});