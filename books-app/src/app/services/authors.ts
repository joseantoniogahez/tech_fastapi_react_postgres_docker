export const fetchAuthors = async () => {
  const response = await fetch("http://localhost:8000/api/authors/");
  if (!response.ok) {
    throw new Error(`Error: ${response.statusText}`);
  }
  return await response.json();
};
