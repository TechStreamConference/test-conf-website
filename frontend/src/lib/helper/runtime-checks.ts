import { imageBothDimensionsSet } from '$logging/events.gen';
import { clientLogger } from '$logging/client';

export function warnIfBothImageDimensionsSet(height?: string, width?: string, url?: string): void {
    if (height !== undefined && width !== undefined) {
        clientLogger.warning(imageBothDimensionsSet({ url, height, width }));
    }
}
