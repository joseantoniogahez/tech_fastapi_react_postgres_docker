import { fetchAuthors } from "@/app/services/authors";
import { Author } from "@/app/types/interfaces";
import React, { useEffect, useState } from "react";

interface BookFilterProps {
  changeAuthorFilter: (id: number | null) => void;
}

const BookFilter: React.FC<BookFilterProps> = ({ changeAuthorFilter }) => {
  const [authorId, setAuthorId] = useState("");
  const [authors, setAuthors] = useState<Array<Author>>([]);

  const getAuthors = async () => {
    const data = await fetchAuthors();
    setAuthors(data);
  };

  const handleAuthorFilterChange = (
    e: React.ChangeEvent<HTMLSelectElement>
  ) => {
    setAuthorId(e.target.value);
    changeAuthorFilter(e.target.value !== "" ? Number(e.target.value) : null);
  };

  useEffect(() => {
    getAuthors();
  }, []);

  return (
    <div className="mb-4">
      <label
        htmlFor="author_filter"
        className="block text-sm font-medium text-gray-700"
      >
        By Author
      </label>
      <select
        id="author_filter"
        value={authorId}
        onChange={handleAuthorFilterChange}
        className="mt-1 block w-full rounded border-gray-300 shadow-sm"
        required
      >
        <option value={""}>Select an Author</option>
        {authors.map((author) => (
          <option key={author.id} value={author.id}>
            {author.name}
          </option>
        ))}
      </select>
    </div>
  );
};

export default BookFilter;
