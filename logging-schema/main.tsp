import "@typespec/json-schema";

using TypeSpec.JsonSchema;

/**
 * Application-level structured log events for the Test Conf website.
 *
 * All models in this namespace are emitted as individual JSON Schema files.
 * The `x-event-name` and `x-event-body` extensions carry the stable event
 * identifier and the human-readable log message body.
 *
 * Events that carry `x-browser-allowed` may be sent by the browser to the
 * frontend log endpoint. Every other event is rejected there.
 * The page the browser was on is not part of the events, the endpoint adds it to the record.
 *
 * Add new events here, then run `just gen-log-schema && just gen-log-models`
 * to regenerate the Pydantic models and Zod schemas.
 */
@jsonSchema
namespace LogEvents {
  // ─── Lifecycle ────────────────────────────────────────────────────────────

  /** Emitted once when the HTTP server has bound to its address. */
  @extension("x-event-name", "application.started")
  @extension("x-event-body", "Application started")
  model ApplicationStarted {
    /** Hostname or IP address the server is listening on. */
    host: string;

    /** TCP port the server is listening on. */
    port: int32;
  }

  /** Emitted when the process receives a shutdown signal. */
  @extension("x-event-name", "application.stopping")
  @extension("x-event-body", "Application stopping")
  model ApplicationStopping {}

  // ─── HTTP ─────────────────────────────────────────────────────────────────

  /** Emitted at the start of every HTTP request handled by the server. */
  @extension("x-event-name", "http.request.received")
  @extension("x-event-body", "HTTP request received")
  model HttpRequestReceived {
    /** HTTP method (GET, POST, …). */
    method: string;

    /** Request path including query string. */
    path: string;

    /** Opaque request correlation identifier, if available. */
    request_id?: string;
  }

  /** Emitted after every HTTP response has been sent. */
  @extension("x-event-name", "http.request.completed")
  @extension("x-event-body", "HTTP request completed")
  model HttpRequestCompleted {
    /** HTTP method (GET, POST, …). */
    method: string;

    /** Request path including query string. */
    path: string;

    /** HTTP response status code. */
    status_code: int32;

    /** Wall-clock time from request receipt to response completion in milliseconds. */
    duration_ms: float64;

    /** Opaque request correlation identifier, if available. */
    request_id?: string;
  }

  // ─── BFF (SvelteKit server-side) ──────────────────────────────────────────

  /** Emitted by the BFF after each call to the backend REST API completes. */
  @extension("x-event-name", "bff.backend_call.completed")
  @extension("x-event-body", "Backend API call completed")
  model BackendCallCompleted {
    /** OpenAPI operationId that was invoked. */
    operation_id: string;

    /** HTTP status code returned by the backend. */
    status_code: int32;

    /** Round-trip duration in milliseconds. */
    duration_ms: float64;

    /** Opaque request correlation identifier, if available. */
    request_id?: string;
  }

  // ─── Frontend helpers ─────────────────────────────────────────────────────

  /** Emitted when an image is rendered with both a width and a height. */
  @extension("x-event-name", "image.both_dimensions_set")
  @extension("x-browser-allowed", true)
  @extension("x-event-body", "Both image dimensions are set, the aspect ratio may be distorted")
  model ImageBothDimensionsSet {
    /** Source URL of the image, if available. */
    url?: string;

    /** The provided height. */
    height: string;

    /** The provided width. */
    width: string;
  }

  /** Emitted when a number that has to be an unsigned integer is not one. */
  @extension("x-event-name", "validator.not_unsigned_int")
  @extension("x-browser-allowed", true)
  @extension("x-event-body", "Value is not an unsigned int, using the default value")
  model ValidatorNotUnsignedInt {
    /** Where the check happened, e.g. the component and the property. */
    origin: string;

    /** The rejected value as text, because NaN and Infinity have no JSON representation. */
    value: string;

    /** The value that is used instead, if there is one. */
    default_value?: float64;
  }

  /** Emitted when a date range is formatted with two different date-time contexts. */
  @extension("x-event-name", "zoned_date_time.mismatched_contexts")
  @extension("x-browser-allowed", true)
  @extension("x-event-body", "Date range formatted with mismatched contexts, using the start context")
  model ZonedDateTimeMismatchedContexts {
    /** Start of the range as an ISO 8601 string in UTC. */
    start_utc: string;

    /** End of the range as an ISO 8601 string in UTC. */
    end_utc: string;

    /** Kind of the start value (`TimeZoneAware` or `TimeZoneUnaware`). */
    start_kind: string;

    /** Kind of the end value (`TimeZoneAware` or `TimeZoneUnaware`). */
    end_kind: string;

    /** Time zone of the start. */
    start_time_zone: string;

    /** Locale of the start. */
    start_locale: string;

    /** Time zone of the end. */
    end_time_zone: string;

    /** Locale of the end. */
    end_locale: string;

    /** The format preset the range was rendered with. */
    format: string;
  }
}
