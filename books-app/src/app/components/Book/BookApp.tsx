import { fetchBooks, removeBook, saveBook } from "@/app/services/books";
import { useCallback, useEffect, useState } from "react";

import { Book, BookPayload } from "@/app/types/interfaces";
import Loader from "../Loader/Loader";
import Toast from "../Toast/Toast";
import BookFilter from "./BookFilter";
import BookTable from "./BookTable";
import CreateBook from "./CreateBook";
import SaveBookForm from "./SaveBookForm";

const BookApp = () => {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUpdate, setShowUpdate] = useState(false);
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [authorFilter, setAuthorFilter] = useState<number | null>(null);

  const getBooks = useCallback(async () => {
    try {
      const data = await fetchBooks(authorFilter);
      setBooks(data);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred");
      }
    } finally {
      setLoading(false);
    }
  }, [authorFilter]);

  const sendSave = async (book: BookPayload) => {
    setLoading(true);
    try {
      await saveBook({
        id: book.id,
        title: book.title,
        year: book.year,
        status: book.status,
        author_id: book.author_id,
        author_name: book.author_name,
      });
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred");
      }
    }
    getBooks();
  };

  const sendDelete = async (id: number) => {
    setLoading(true);
    try {
      await removeBook(id);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred");
      }
    }
    getBooks();
  };

  const closeUpdateForm = () => setShowUpdate(false);
  const openUpdateForm = (book: Book) => {
    setShowUpdate(true);
    setSelectedBook(book);
  };

  const removeErrorMessage = () => setError("");

  const changeAuthorFilter = (author_id: number | null) =>
    setAuthorFilter(author_id);

  useEffect(() => {
    getBooks();
  }, [getBooks]);

  if (loading) return <Loader />;

  return (
    <div className="w-full p-8">
      <main className="">
        <p className="text-2xl pb-8">Books App</p>
        <BookFilter changeAuthorFilter={changeAuthorFilter} />
        <BookTable
          books={books}
          openUpdateForm={openUpdateForm}
          sendDelete={sendDelete}
        />
        <CreateBook sendSave={sendSave} />
        {showUpdate && (
          <SaveBookForm
            book={selectedBook}
            handleClose={closeUpdateForm}
            sendSave={sendSave}
          />
        )}
        {error && <Toast message={error} onClose={removeErrorMessage}></Toast>}
      </main>
    </div>
  );
};

export default BookApp;
