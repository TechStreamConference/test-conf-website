export enum Theme {
	System = 'system',
	Light = 'light',
	Dark = 'dark'
}

// when changing these: remember that there are corresponding values in 'src/app.html' and 'static/main.css'
const STORAGE_KEY: string = 'TEST_CONF_THEME';
const CSS_DARK_MODE: string = 'dark-theme';
const CSS_LIGHT_MODE: string = 'light-theme';
const CSS_TRANSITION_CLASS: string = 'theme-transition';
const CSS_TRANSITION_TIME_MILLISECONDS: number = 500;
const PREFERRED_THEME_QUERY: string = '(prefers-color-scheme: dark)';

let css_transition_timer: number | undefined;
let initialized: boolean = false;

function parseTheme(value: string | null): Theme {
	switch (value) {
		case Theme.Light:
			return Theme.Light;

		case Theme.Dark:
			return Theme.Dark;

		case Theme.System:
		default:
			return Theme.System;
	}
}

function nextTheme(theme: Theme): Theme {
	switch (theme) {
		case Theme.Dark:
			return Theme.Light;
		case Theme.Light:
			return Theme.System;
		case Theme.System:
		default:
			return Theme.Dark;
	}
}

/**
 * @brief Saves the theme to the browsers' local storage.
 * @param theme the enum value
 */
function saveTheme(theme: Theme): void {
	localStorage.setItem(STORAGE_KEY, theme);
}

/**
 * @brief Applies the theme to the document.
 * @param theme the enum value
 */
function applyTheme(theme: Theme): void {
	const root = document.documentElement;
	root.classList.remove(CSS_LIGHT_MODE, CSS_DARK_MODE);

	switch (theme) {
		case Theme.Light:
			root.classList.add(CSS_LIGHT_MODE);
			break;

		case Theme.Dark:
			root.classList.add(CSS_DARK_MODE);
			break;

		case Theme.System:
		default:
			// no css class. Browser follows user preference.
			break;
	}
}

/**
 * @brief Applies the css theme transition class to the document.
 * Sets a time as long as the css transition is active.
 * Removes the css transition class once the transition is done.
 */
function applyTransition(): void {
	const root = document.documentElement;
	root.classList.add(CSS_TRANSITION_CLASS);

	if (css_transition_timer !== undefined) {
		clearTimeout(css_transition_timer);
	}

	css_transition_timer = window.setTimeout(() => {
		root.classList.remove(CSS_TRANSITION_CLASS);
		css_transition_timer = undefined;
	}, CSS_TRANSITION_TIME_MILLISECONDS);
}

/**
 * @brief Initializes the theme.
 * Also sets an event listener for the system theme change.
 */
export function initTheme(): void {
	if (initialized) {
		return;
	}

	applyTheme(getTheme());
	window.matchMedia(PREFERRED_THEME_QUERY).addEventListener('change', () => {
		if (getTheme() === Theme.System) {
			applyTheme(Theme.System);
			applyTransition();
		}
	});

	initialized = true;
}

/**
 * @brief Gets the theme from the browsers' local storage and parses it.
 * @returns the enum value
 */
export function getTheme(): Theme {
	return parseTheme(localStorage.getItem(STORAGE_KEY));
}

/**
 * @brief Sets the theme in the browsers' local storage and applies it to the document.
 * @param theme the enum value
 */
export function setTheme(theme: Theme): void {
	saveTheme(theme);
	applyTheme(theme);
	applyTransition();
}

/**
 * @brief Toggles the theme and returns the new theme.
 * @returns the new theme
 */
export function toggleTheme(): Theme {
	const next = nextTheme(getTheme());
	setTheme(next);
	return next;
}
