/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{}} Test_PlainInputs */

const de_test_plain = /** @type {(inputs: Test_PlainInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Gültiger Test-Text`)
};

const en_test_plain = /** @type {(inputs: Test_PlainInputs) => LocalizedString} */ () => {
	return /** @type {LocalizedString} */ (`Valid test text`)
};

/**
* | output |
* | --- |
* | "Valid test text" |
*
* @param {Test_PlainInputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
export const test_plain = /** @type {((inputs?: Test_PlainInputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Test_PlainInputs, { locale?: "de" | "en" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_test_plain(inputs)
	return en_test_plain(inputs)
});