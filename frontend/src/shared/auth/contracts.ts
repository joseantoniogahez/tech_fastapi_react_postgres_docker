import {
  expectBooleanField,
  expectLiteralStringField,
  expectNumberField,
  expectRecord,
  expectStringField,
} from "@/shared/api/contracts";

export interface AuthenticatedUser {
  id: number;
  username: string;
  disabled: boolean;
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
