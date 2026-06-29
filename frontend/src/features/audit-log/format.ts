export const formatAuditLogTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  return date.toISOString().replace(".000Z", " UTC").replace("Z", " UTC");
};
