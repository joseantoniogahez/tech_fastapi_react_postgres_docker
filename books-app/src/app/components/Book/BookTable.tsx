import { Book } from "@/app/types/interfaces";
import React from "react";
import BookRow from "./BookRow";

interface BookTableProps {
  books: Array<Book>;
  openUpdateForm: (book: Book) => void;
  sendDelete: (id: number) => void;
}

const BookTable: React.FC<BookTableProps> = ({
  books,
  openUpdateForm,
  sendDelete,
}) => {
  return (
    <table className="border-collapse border border-slate-500  w-full">
      <thead>
        <tr>
          <th className="border border-slate-600 text-left">Title</th>
          <th className="border border-slate-600 text-left">Year</th>
          <th className="border border-slate-600 text-left">Status</th>
          <th className="border border-slate-600 text-left">Author</th>
          <th className="border border-slate-600 text-left">Actions</th>
        </tr>
      </thead>
      <tbody className="table-row-group">
        {books.map((book) => (
          <BookRow
            key={`book-${book.id}`}
            book={book}
            openUpdateForm={openUpdateForm}
            sendDelete={sendDelete}
          />
        ))}
      </tbody>
    </table>
  );
};

export default BookTable;
