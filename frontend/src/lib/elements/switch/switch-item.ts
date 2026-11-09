import type { Snippet } from 'svelte';

export interface SwitchItem<T> {
    value: T;
    label: string;
    icon: Snippet<[T]>;
}
