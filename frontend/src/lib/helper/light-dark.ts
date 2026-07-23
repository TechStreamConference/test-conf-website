export enum Theme {
	System = 'system',
	Light = 'light',
	Dark = 'dark'
}

// when changing these: remember, that there are coresponding valus in 'src/app.html' and 'static/main.css'
const STORAGE_KEY: string = 'TEST_CONF_THEME';
const CSS_DARK_MODE: string = 'dark-theme';
const CSS_LIGHT_MODE: string = 'light-theme';
const CSS_TRANSITION_CLASS: string = 'theme-transition';
const CSS_TRANSITION_TIME: number = 500;
const PREFERRED_THEME_QUERY: string = '(prefers-color-scheme: dark)';

let css_transition_timer: number | undefined;
let initialized: boolean = false;

function parse_theme(value: string | null): Theme {
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

function next_theme(theme: Theme): Theme {
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

function save_theme(theme: Theme): void {
	localStorage.setItem(STORAGE_KEY, theme);
}

function apply_theme(theme: Theme): void {
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

function apply_transition(): void {
	const root = document.documentElement;
	root.classList.add(CSS_TRANSITION_CLASS);

	if (css_transition_timer !== undefined) {
		clearTimeout(css_transition_timer);
	}

	css_transition_timer = window.setTimeout(() => {
		root.classList.remove(CSS_TRANSITION_CLASS);
		css_transition_timer = undefined;
	}, CSS_TRANSITION_TIME);
}

export function init_theme(): void {
	if (initialized) {
		return;
	}

	initialized = true;
	apply_theme(get_theme());

	window.matchMedia(PREFERRED_THEME_QUERY).addEventListener('change', () => {
		if (get_theme() === Theme.System) {
			apply_theme(Theme.System);
			apply_transition();
		}
	});
}

export function get_theme(): Theme {
	return parse_theme(localStorage.getItem(STORAGE_KEY));
}

export function set_theme(theme: Theme): void {
	save_theme(theme);
	apply_theme(theme);
	apply_transition();
}

export function toggle_theme(): Theme {
	const next = next_theme(get_theme());
	set_theme(next);
	return next;
}
