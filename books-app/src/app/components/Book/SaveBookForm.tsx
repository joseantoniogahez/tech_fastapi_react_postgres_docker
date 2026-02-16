import { fetchAuthors } from "@/app/services/authors";
import { Author, Book, BookPayload, Status } from "@/app/types/interfaces";
import React, { useEffect, useState } from "react";

interface SaveBookFormProps {
  book: Book | null;
  handleClose: () => void;
  sendSave: (book: BookPayload) => void;
}

const SaveBookForm: React.FC<SaveBookFormProps> = ({
  book,
  handleClose,
  sendSave,
}) => {
  const [title, setTitle] = useState(book?.title || "");
  const [year, setYear] = useState(book?.year || "");
  const [status, setStatus] = useState(book?.status || "");
  const [authorId, setAuthorId] = useState(book?.author.id || "");
  const [authorName, setAuthorName] = useState(book?.author.name || "");
  const [authors, setAuthors] = useState<Array<Author>>([]);
  const [isNewAuthor, setIsNewAuthor] = useState(false);

  const handleNewAuthor = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    if (value === "new") {
      setIsNewAuthor(true);
      setAuthorId("");
      setAuthorName("");
    } else {
      setIsNewAuthor(false);
      const selectedAuthor = authors.find(
        (author) => author.id === parseInt(value, 10)
      );
      setAuthorId(selectedAuthor?.id || "");
      setAuthorName(selectedAuthor?.name || "");
    }
  };

  const handleSaveBookForm = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    sendSave({
      id: book?.id,
      title: title,
      year: Number(year),
      status: status as Status,
      author_id: Number(authorId),
      author_name: authorName,
    });
    handleClose();
  };

  useEffect(() => {
    let isMounted = true;
    void Promise.resolve(fetchAuthors()).then((data) => {
      if (isMounted) {
        setAuthors(data);
      }
    });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-96 p-6 relative">
        <h2 className="text-lg font-semibold mb-4">
          {book ? "Update Book" : "Create Book"}
        </h2>
        <form onSubmit={handleSaveBookForm}>
          <div className="mb-4">
            <label
              htmlFor="title"
              className="block text-sm font-medium text-gray-700"
            >
              Title
            </label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="mt-1 block w-full rounded border-gray-300 shadow-sm"
              required
            />
          </div>
          <div className="mb-4">
            <label
              htmlFor="year"
              className="block text-sm font-medium text-gray-700"
            >
              Year
            </label>
            <input
              id="year"
              type="number"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              className="mt-1 block w-full rounded border-gray-300 shadow-sm"
              required
            />
          </div>
          <div className="mb-4">
            <label
              htmlFor="status"
              className="block text-sm font-medium text-gray-700"
            >
              Status
            </label>
            <select
              id="status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="mt-1 block w-full rounded border-gray-300 shadow-sm"
              required
            >
              <option value="">Select an Status</option>
              <option value="published">Published</option>
              <option value="draft">Draft</option>
            </select>
          </div>
          <div className="mb-4">
            <label
              htmlFor="author"
              className="block text-sm font-medium text-gray-700"
            >
              Author
            </label>
            <select
              id="author"
              value={isNewAuthor ? "new" : authorId}
              onChange={handleNewAuthor}
              className="mt-1 block w-full rounded border-gray-300 shadow-sm"
              required
            >
              <option value={""}>Select an Author</option>
              {authors.map((author) => (
                <option key={author.id} value={author.id}>
                  {author.name}
                </option>
              ))}
              <option value="new">[Add new author]</option>
            </select>
            {isNewAuthor && (
              <div className="mt-4">
                <label
                  htmlFor="newAuthor"
                  className="block text-sm font-medium text-gray-700"
                >
                  New Author Name
                </label>
                <input
                  id="newAuthor"
                  type="text"
                  value={authorName}
                  onChange={(e) => setAuthorName(e.target.value)}
                  className="mt-1 block w-full rounded border-gray-300 shadow-sm"
                  required
                />
              </div>
            )}
          </div>

          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
              aria-label="Cancel"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
              aria-label="Save"
            >
              {book?.id ? "Update" : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SaveBookForm;
