namespace AspBase.Api.Common;

/// <summary>Uniform error payload: <c>{ "error": "..." }</c>, matching the DRF views.</summary>
public record ErrorResponse(string Error);

/// <summary>Uniform message payload: <c>{ "message": "..." }</c>.</summary>
public record MessageResponse(string Message);
