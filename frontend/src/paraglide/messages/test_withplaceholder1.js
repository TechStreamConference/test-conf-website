/* eslint-disable */
import { getLocale, experimentalStaticLocale } from '../runtime.js';

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */

/** @typedef {{ placeholder1: NonNullable<unknown>, placeholder2: NonNullable<unknown> }} Test_Withplaceholder1Inputs */

const de_test_withplaceholder1 = /** @type {(inputs: Test_Withplaceholder1Inputs) => LocalizedString} */ (i) => {
	return /** @type {LocalizedString} */ (`Gültiger Testtext mit Lücke '${i?.placeholder1}' : '${i?.placeholder2}'`)
};

const en_test_withplaceholder1 = /** @type {(inputs: Test_Withplaceholder1Inputs) => LocalizedString} */ (i) => {
	return /** @type {LocalizedString} */ (`Valid test text with placeholder: '${i?.placeholder2}' : '${i?.placeholder1}'`)
};

/**
* | output |
* | --- |
* | "Valid test text with placeholder: '{placeholder2}' : '{placeholder1}'" |
*
* @param {Test_Withplaceholder1Inputs} inputs
* @param {{ locale?: "de" | "en" }} options
* @returns {LocalizedString}
*/
const test_withplaceholder1 = /** @type {((inputs: Test_Withplaceholder1Inputs, options?: { locale?: "de" | "en" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Test_Withplaceholder1Inputs, { locale?: "de" | "en" }, {}>} */ ((inputs, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "de") return de_test_withplaceholder1(inputs)
	return en_test_withplaceholder1(inputs)
});
export { test_withplaceholder1 as "test_withPlaceholder" }