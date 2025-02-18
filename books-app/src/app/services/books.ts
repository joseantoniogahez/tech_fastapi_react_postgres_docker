import { BookPayload } from "../types/interfaces";

export const fetchBooks = async (authorFilter: number | null) => {
  const url = new URL("http://localhost:8000/api/books/");
  if (authorFilter !== null) {
    url.searchParams.append("author_id", authorFilter.toString());
  }
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Error: ${response.statusText}`);
  }
  return await response.json();
};

export const saveBook = async (book: BookPayload) => {
  let response = undefined;
  if (book?.id)
    response = await fetch(`http://localhost:8000/api/books/${book.id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(book),
    });
  else
    response = await fetch("http://localhost:8000/api/books/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(book),
    });

  if (!response.ok) {
    throw new Error(`Error: ${response.statusText}`);
  }
  return await response.json();
};

export const removeBook = async (id: number) => {
  if (id) {
    const response = await fetch(`http://localhost:8000/api/books/${id}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      throw new Error(`Error: ${response.statusText}`);
    }
  }
};
