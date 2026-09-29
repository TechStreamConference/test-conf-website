/**
 * @brief Thrown when a backend call returns an error response. Carries the error payload.
 */
export class GenericBackendError<T = unknown> extends Error {
    error: T;
    constructor(message: string, error: T) {
        super(message);
        this.name = 'GenericBackendError';
        this.error = error;
    }
}

/**
 * @brief Thrown when a backend call succeeded but did not return any data.
 */
export class UndefinedDataError extends Error {
    constructor(message: string) {
        super(message);
        this.name = 'UndefinedDataError';
    }
}

/**
 * @brief Thrown when ZonedDates differ in context.
 */
export class MissmatchZonedDateTimeContextError extends Error {
    startLocal: string;
    startTimezone: string;
    endLocal: string;
    endTimezone: string;

    constructor(
        message: string,
        startLocal: string,
        startTimezone: string,
        endLocal: string,
        endTimezone: string
    ) {
        super(message);
        this.name = 'MissmatchZonedDateTimeContextError';
        this.startLocal = startLocal;
        this.startTimezone = startTimezone;
        this.endLocal = endLocal;
        this.endTimezone = endTimezone;
    }
}
