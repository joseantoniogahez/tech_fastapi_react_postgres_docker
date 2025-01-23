import { BookPayload } from "./interfaces";

export const fetchAuthors = async () => {
  const response = await fetch("http://localhost:8000/api/authors/");
  if (!response.ok) {
    throw new Error(`Error: ${response.statusText}`);
  }
  return await response.json();
};

export const fetchBooks = async () => {
  const response = await fetch("http://localhost:8000/api/books/");
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
