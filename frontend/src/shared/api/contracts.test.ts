import {
  ApiContractError,
  expectBooleanField,
  expectLiteralStringField,
  expectNumberField,
  expectRecord,
  expectStringField,
} from "@/shared/api/contracts";

describe("api contract helpers", () => {
  it("accepts valid object payloads", () => {
    expect(expectRecord({ ok: true }, "Payload")).toEqual({ ok: true });
  });

  it("rejects invalid payload types with descriptive type names", () => {
    expect(() => expectRecord(null, "Payload")).toThrowError(
      new ApiContractError("Payload: expected object payload, received null"),
    );
    expect(() => expectRecord(["a"], "Payload")).toThrowError(
      new ApiContractError("Payload: expected object payload, received array"),
    );
    expect(() => expectRecord("bad", "Payload")).toThrowError(
      new ApiContractError("Payload: expected object payload, received string"),
    );
  });

  it("validates string fields and min-length rules", () => {
    const record = { name: "john", short: "x", age: 10 } as const;

    expect(expectStringField(record, "name", "User")).toBe("john");
    expect(() => expectStringField(record, "short", "User", { minLength: 2 })).toThrowError(
      new ApiContractError("User: field 'short' must have length >= 2"),
    );
    expect(() => expectStringField(record, "age", "User")).toThrowError(
      new ApiContractError("User: field 'age' must be string, received number"),
    );
    expect(() => expectStringField(record, "missing", "User")).toThrowError(
      new ApiContractError("User: missing required field 'missing'"),
    );
  });

  it("validates number fields and rejects NaN", () => {
    const record = { valid: 5, invalid: Number.NaN, text: "5" } as const;

    expect(expectNumberField(record, "valid", "Metric")).toBe(5);
    expect(() => expectNumberField(record, "invalid", "Metric")).toThrowError(
      new ApiContractError("Metric: field 'invalid' must be number, received number"),
    );
    expect(() => expectNumberField(record, "text", "Metric")).toThrowError(
      new ApiContractError("Metric: field 'text' must be number, received string"),
    );
  });

  it("validates boolean fields", () => {
    const record = { ok: true, text: "true" } as const;

    expect(expectBooleanField(record, "ok", "Flag")).toBe(true);
    expect(() => expectBooleanField(record, "text", "Flag")).toThrowError(
      new ApiContractError("Flag: field 'text' must be boolean, received string"),
    );
  });

  it("validates literal string fields", () => {
    const record = { token_type: "bearer", wrong: "other", empty: "" } as const;

    expect(expectLiteralStringField(record, "token_type", "Token", "bearer")).toBe("bearer");
    expect(() => expectLiteralStringField(record, "wrong", "Token", "bearer")).toThrowError(
      new ApiContractError("Token: field 'wrong' must equal 'bearer', received 'other'"),
    );
    expect(() => expectLiteralStringField(record, "empty", "Token", "bearer")).toThrowError(
      new ApiContractError("Token: field 'empty' must have length >= 1"),
    );
  });
});
