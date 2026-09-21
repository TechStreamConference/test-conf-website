//
// Tech Stream Conference
// 2026
//
// Runtime checks for component properties.
//

export function warnIfBothImageDimensionsSet(height?: string, width?: string, url?: string): void {
    if (height !== undefined && width !== undefined) {
        console.warn(
            'IMAGE: Both width and height are provided.' +
                'Providing both dimensions may distort the image aspect ratio.',
            url
        );
    }
}
