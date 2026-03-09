import {
  ApiContractError,
  expectBooleanField,
  expectLiteralStringField,
  expectNumberField,
  expectRecord,
  expectStringField,
} from "@/shared/api/contracts";

const describeType = (value: unknown): string => {
  if (value === null) {
    return "null";
  }
  if (Array.isArray(value)) {
    return "array";
  }
  return typeof value;
};

const expectStringArrayField = (record: Record<string, unknown>, field: string, context: string): string[] => {
  if (!(field in record)) {
    throw new ApiContractError(`${context}: missing required field '${field}'`);
  }

  const value = record[field];
  if (!Array.isArray(value)) {
    throw new ApiContractError(`${context}: field '${field}' must be array, received ${describeType(value)}`);
  }

  return value.map((item, index) => {
    if (typeof item !== "string") {
      throw new ApiContractError(
        `${context}: field '${field}[${index}]' must be string, received ${describeType(item)}`,
      );
    }
    if (!item.length) {
      throw new ApiContractError(`${context}: field '${field}[${index}]' must have length >= 1`);
    }
    return item;
  });
};

export interface AuthenticatedUser {
  id: number;
  username: string;
  disabled: boolean;
  permissions: string[];
}

export interface AccessTokenResponse {
  access_token: string;
  token_type: "bearer";
}

export const parseAuthenticatedUser = (payload: unknown): AuthenticatedUser => {
  const context = "AuthenticatedUser";
  const record = expectRecord(payload, context);

  return {
    id: expectNumberField(record, "id", context),
    username: expectStringField(record, "username", context, { minLength: 1 }),
    disabled: expectBooleanField(record, "disabled", context),
    permissions: expectStringArrayField(record, "permissions", context),
  };
};

export const parseAccessTokenResponse = (payload: unknown): AccessTokenResponse => {
  const context = "AccessTokenResponse";
  const record = expectRecord(payload, context);

  return {
    access_token: expectStringField(record, "access_token", context, { minLength: 1 }),
    token_type: expectLiteralStringField(record, "token_type", context, "bearer"),
  };
};
