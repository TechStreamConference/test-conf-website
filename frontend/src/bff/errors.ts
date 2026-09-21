//
// Tech Stream Conference
// 2026
//
// Error types for failed backend calls.
//

export class GenericBackendError<T = unknown> extends Error {
    error: T;
    constructor(message: string, error: T) {
        super(message);
        this.name = 'GenericBackendError';
        this.error = error;
    }
}

export class UndefinedDataError extends Error {
    constructor(message: string) {
        super(message);
        this.name = 'UndefinedDataError';
    }
}
