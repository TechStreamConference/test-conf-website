import "@typespec/json-schema";

using TypeSpec.JsonSchema;

/**
 * Application-level structured log events for the Test Conf website.
 *
 * All models in this namespace are emitted as individual JSON Schema files.
 * The `x-event-name` and `x-event-body` extensions carry the stable event
 * identifier and the human-readable log message body.
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
}
