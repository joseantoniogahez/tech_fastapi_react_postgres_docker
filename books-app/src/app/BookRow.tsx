import React from "react";
import { StatusEnum } from "./consts";
import { Book } from "./interfaces";

interface BookRowProps {
  book: Book;
  openUpdateForm: (book: Book) => void;
  sendDelete: (id: number) => void;
}

const BookRow: React.FC<BookRowProps> = ({
  book,
  openUpdateForm,
  sendDelete,
}) => {
  const onEdit = () => {
    openUpdateForm(book);
  };
  const onDelete = () => {
    sendDelete(book.id);
  };

  return (
    <tr>
      <td className="border border-slate-700">{book.title}</td>
      <td className="border border-slate-700">{book.year}</td>
      <td className="border border-slate-700">
        {StatusEnum[book.status] || book.status}
      </td>
      <td className="border border-slate-700">{book.author.name}</td>
      <td className="border w-56 border-slate-700 space-x-4 ">
        <button
          onClick={onEdit}
          className="px-4 py-2 w-24 bg-blue-500 text-white rounded-md hover:bg-blue-600"
        >
          Edit
        </button>
        <button
          onClick={onDelete}
          className="px-4 py-2 w-24 bg-red-500 text-white rounded-md hover:bg-red-600"
        >
          Delete
        </button>
      </td>
    </tr>
  );
};

export default BookRow;
