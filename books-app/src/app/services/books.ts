import { BookPayload } from "../types/interfaces";
import { buildApiUrl } from "./api";

export const fetchBooks = async (authorFilter: number | null) => {
  const searchParams = new URLSearchParams();
  if (authorFilter !== null) {
    searchParams.append("author_id", authorFilter.toString());
  }
  const queryString = searchParams.toString();
  const response = await fetch(
    `${buildApiUrl("/books/")}${queryString ? `?${queryString}` : ""}`
  );
  if (!response.ok) {
    throw new Error(`Error: ${response.statusText}`);
  }
  return await response.json();
};

export const saveBook = async (book: BookPayload) => {
  let response = undefined;
  if (book?.id)
    response = await fetch(buildApiUrl(`/books/${book.id}`), {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(book),
    });
  else
    response = await fetch(buildApiUrl("/books/"), {
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
    const response = await fetch(buildApiUrl(`/books/${id}`), {
      method: "DELETE",
    });
    if (!response.ok) {
      throw new Error(`Error: ${response.statusText}`);
    }
  }
};
