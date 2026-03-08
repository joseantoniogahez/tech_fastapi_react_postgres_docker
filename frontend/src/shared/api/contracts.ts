const describeType = (value: unknown): string => {
  if (value === null) {
    return "null";
  }

  if (Array.isArray(value)) {
    return "array";
  }

  return typeof value;
};

export class ApiContractError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiContractError";
  }
}

type ContractRecord = Record<string, unknown>;

export const expectRecord = (payload: unknown, context: string): ContractRecord => {
  if (typeof payload !== "object" || payload === null || Array.isArray(payload)) {
    throw new ApiContractError(`${context}: expected object payload, received ${describeType(payload)}`);
  }

  return payload as ContractRecord;
};

const expectField = (record: ContractRecord, field: string, context: string): unknown => {
  if (!(field in record)) {
    throw new ApiContractError(`${context}: missing required field '${field}'`);
  }

  return record[field];
};

export const expectStringField = (
  record: ContractRecord,
  field: string,
  context: string,
  options: { minLength?: number } = {},
): string => {
  const value = expectField(record, field, context);
  if (typeof value !== "string") {
    throw new ApiContractError(`${context}: field '${field}' must be string, received ${describeType(value)}`);
  }

  const minLength = options.minLength ?? 0;
  if (value.length < minLength) {
    throw new ApiContractError(`${context}: field '${field}' must have length >= ${minLength}`);
  }

  return value;
};

export const expectNumberField = (record: ContractRecord, field: string, context: string): number => {
  const value = expectField(record, field, context);
  if (typeof value !== "number" || Number.isNaN(value)) {
    throw new ApiContractError(`${context}: field '${field}' must be number, received ${describeType(value)}`);
  }
  return value;
};

export const expectBooleanField = (record: ContractRecord, field: string, context: string): boolean => {
  const value = expectField(record, field, context);
  if (typeof value !== "boolean") {
    throw new ApiContractError(`${context}: field '${field}' must be boolean, received ${describeType(value)}`);
  }
  return value;
};

export const expectLiteralStringField = (
  record: ContractRecord,
  field: string,
  context: string,
  literal: string,
): string => {
  const value = expectStringField(record, field, context, { minLength: 1 });
  if (value !== literal) {
    throw new ApiContractError(`${context}: field '${field}' must equal '${literal}', received '${value}'`);
  }
  return value;
};
