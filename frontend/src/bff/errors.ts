export class UndefinedDataError extends Error {
	constructor(message: string) {
		super(message);
		this.name = 'UndefinedDataError';
	}
}
