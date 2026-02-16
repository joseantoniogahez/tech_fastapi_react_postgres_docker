import { buildApiUrl } from "./api";

export const fetchAuthors = async () => {
  const response = await fetch(buildApiUrl("/authors/"));
  if (!response.ok) {
    throw new Error(`Error: ${response.statusText}`);
  }
  return await response.json();
};
