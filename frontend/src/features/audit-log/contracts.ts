import {
  ApiContractError,
  expectNumberField,
  expectRecord,
  expectStringField,
} from "@/shared/api/contracts";

const expectNullableNumberField = (
  record: Record<string, unknown>,
  field: string,
  context: string,
): number | null => {
  if (!(field in record)) {
    throw new ApiContractError(`${context}: missing required field '${field}'`);
  }

  const value = record[field];
  if (value === null) {
    return null;
  }
  if (typeof value !== "number" || Number.isNaN(value)) {
    throw new ApiContractError(`${context}: invalid nullable number '${field}'`);
  }
  return value;
};

const expectNullableStringField = (
  record: Record<string, unknown>,
  field: string,
  context: string,
): string | null => {
  if (!(field in record)) {
    throw new ApiContractError(`${context}: missing required field '${field}'`);
  }

  const value = record[field];
  if (value === null) {
    return null;
  }
  if (typeof value !== "string") {
    throw new ApiContractError(`${context}: invalid nullable string '${field}'`);
  }
  return value;
};

export interface AuditLogEntry {
  id: number;
  actor_user_id: number | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  summary: string;
  created_at: string;
}

export const parseAuditLogEntry = (payload: unknown): AuditLogEntry => {
  const context = "AuditLogEntry";
  const record = expectRecord(payload, context);

  return {
    id: expectNumberField(record, "id", context),
    actor_user_id: expectNullableNumberField(record, "actor_user_id", context),
    action: expectStringField(record, "action", context, { minLength: 1 }),
    resource_type: expectStringField(record, "resource_type", context, { minLength: 1 }),
    resource_id: expectNullableStringField(record, "resource_id", context),
    summary: expectStringField(record, "summary", context, { minLength: 1 }),
    created_at: expectStringField(record, "created_at", context, { minLength: 1 }),
  };
};

export const parseAuditLogEntryList = (payload: unknown): AuditLogEntry[] => {
  if (!Array.isArray(payload)) {
    throw new ApiContractError("AuditLogEntryList: expected array payload");
  }

  return payload.map(parseAuditLogEntry);
};
