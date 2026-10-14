/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{}} Header_Menu_AriaInputs */

const de_header_menu_aria = /** @type {(inputs: Header_Menu_AriaInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Hauptmenü`)
};

const en_header_menu_aria = /** @type {(inputs: Header_Menu_AriaInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Main menu`)
};

/**
* | output |
* | --- |
* | "Main menu" |
*
* @param {Header_Menu_AriaInputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
export const header_menu_aria = /** @type {((inputs?: Header_Menu_AriaInputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Header_Menu_AriaInputs, { locale?: "de" | "en" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_header_menu_aria(inputs)
	return en_header_menu_aria(inputs)
});