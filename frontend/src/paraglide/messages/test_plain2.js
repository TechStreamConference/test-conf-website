/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{}} Test_Plain2Inputs */

const de_test_plain2 = /** @type {(inputs: Test_Plain2Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Zweiter gültiger Test-Text`)
};

const en_test_plain2 = /** @type {(inputs: Test_Plain2Inputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`second valid test text`)
};

/**
* | output |
* | --- |
* | "second valid test text" |
*
* @param {Test_Plain2Inputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
export const test_plain2 = /** @type {((inputs?: Test_Plain2Inputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Test_Plain2Inputs, { locale?: "de" | "en" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_test_plain2(inputs)
	return en_test_plain2(inputs)
});