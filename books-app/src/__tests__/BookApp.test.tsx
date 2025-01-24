import BookApp from "@/app/components/Book/BookApp";
import { fetchAuthors } from "@/app/services/authors";
import { fetchBooks, removeBook, saveBook } from "@/app/services/books";
import "@testing-library/jest-dom";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";

jest.mock("@/app/services/authors");
jest.mock("@/app/services/books");

const mockedFetchAuthors = fetchAuthors as jest.Mock;
const mockedFetchBooks = fetchBooks as jest.Mock;
const mockedSaveBook = saveBook as jest.Mock;
const mockedRemoveBook = removeBook as jest.Mock;

describe("BookApp Component", () => {
  beforeEach(() => {
    mockedSaveBook.mockClear();
  });

  it("renders and fetches books successfully", async () => {
    const mockBooks = [
      {
        id: 1,
        title: "Foundation",
        year: 1950,
        status: "published",
        author: { id: 1, name: "Isaac Asimov" },
      },
      {
        id: 2,
        title: "The Lion, the Witch and the Wardrobe",
        year: 1951,
        status: "published",
        author: { id: 2, name: "C.S. Lewis" },
      },
    ];

    mockedFetchBooks.mockResolvedValue(mockBooks);

    render(<BookApp />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Foundation")).toBeInTheDocument();
      expect(
        screen.getByText("The Lion, the Witch and the Wardrobe")
      ).toBeInTheDocument();

      const rows = screen.getAllByRole("row");
      expect(rows).toHaveLength(3);
    });

    expect(screen.getByText(/books app/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create/i })).toBeInTheDocument();
  });

  it("opens the SaveBook form when clicking the Create button", async () => {
    const mockAuthors = [{ id: 1, name: "Isaac Asimov" }];
    const book = {
      id: undefined,
      title: "Python for dummies",
      year: 2025,
      status: "draft",
      author: { id: 0, name: "Jose Antonio" },
    };

    mockedFetchBooks.mockResolvedValue([]);
    mockedFetchAuthors.mockResolvedValue(mockAuthors);
    mockedSaveBook.mockResolvedValue({});

    render(<BookApp />);
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /create/i })
      ).toBeInTheDocument();
    });

    const createButton = screen.getByRole("button", { name: /create/i });
    await act(async () => {
      fireEvent.click(createButton);
    });

    expect(screen.getByText(/create book/i)).toBeInTheDocument();

    expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/year/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/status/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^author$/i)).toBeInTheDocument();

    expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
    const saveButton = screen.getByRole("button", { name: /save/i });
    expect(saveButton).toBeInTheDocument();
    expect(saveButton).toHaveTextContent("Create");

    fireEvent.change(screen.getByLabelText(/title/i), {
      target: { value: book.title },
    });
    fireEvent.change(screen.getByLabelText(/year/i), {
      target: { value: book.year },
    });
    fireEvent.change(screen.getByLabelText(/status/i), {
      target: { value: book.status },
    });
    fireEvent.change(screen.getByLabelText(/^author$/i), {
      target: { value: "new" },
    });
    fireEvent.change(screen.getByLabelText(/new author name/i), {
      target: { value: book.author.name },
    });

    await act(async () => {
      fireEvent.click(saveButton);
    });
    expect(mockedSaveBook).toHaveBeenCalledTimes(1);
    expect(mockedSaveBook).toHaveBeenCalledWith({
      id: book.id,
      title: book.title,
      year: book.year,
      status: book.status,
      author_id: book.author.id,
      author_name: book.author.name,
    });
  });

  it("renders and allows editing a book", async () => {
    const mockBooks = [
      {
        id: 1,
        title: "Foundation",
        year: 1950,
        status: "published",
        author: { id: 1, name: "Isaac Asimov" },
      },
    ];

    const mockAuthors = [{ id: 1, name: "Isaac Asimov" }];

    const new_title = "Foundation (Traducido)";

    mockedFetchBooks.mockResolvedValue(mockBooks);
    mockedFetchAuthors.mockResolvedValue(mockAuthors);
    mockedSaveBook.mockResolvedValue({});

    render(<BookApp />);

    await waitFor(() => {
      expect(screen.getByText(mockBooks[0].title)).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /edit/i }));
    });

    await waitFor(() => {
      expect(screen.getByText(/update book/i)).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/title/i)).toHaveValue(mockBooks[0].title);
    expect(screen.getByLabelText(/year/i)).toHaveValue(mockBooks[0].year);
    expect(screen.getByLabelText(/status/i)).toHaveValue(mockBooks[0].status);
    expect(screen.getByLabelText(/^author$/i)).toHaveValue(
      mockBooks[0].author.id.toString()
    );

    expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
    const saveButton = screen.getByRole("button", { name: /save/i });
    expect(saveButton).toBeInTheDocument();
    expect(saveButton).toHaveTextContent("Update");

    fireEvent.change(screen.getByLabelText(/title/i), {
      target: { value: new_title },
    });

    await act(async () => {
      fireEvent.click(saveButton);
    });

    expect(mockedSaveBook).toHaveBeenCalledTimes(1);
    expect(mockedSaveBook).toHaveBeenCalledWith({
      id: mockBooks[0].id,
      title: new_title,
      year: mockBooks[0].year,
      status: mockBooks[0].status,
      author_id: mockBooks[0].author.id,
      author_name: mockBooks[0].author.name,
    });
  });

  it("renders and allows deleting a book", async () => {
    const mockBooks = [
      {
        id: 1,
        title: "Foundation",
        year: 1950,
        status: "published",
        author: { id: 1, name: "Isaac Asimov" },
      },
    ];

    mockedFetchBooks.mockResolvedValue(mockBooks);
    mockedRemoveBook.mockResolvedValue({});

    render(<BookApp />);

    await waitFor(() => {
      expect(screen.getByText(mockBooks[0].title)).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /delete/i }));
    });

    expect(mockedRemoveBook).toHaveBeenCalledTimes(1);
    expect(mockedRemoveBook).toHaveBeenCalledWith(mockBooks[0].id);
  });
});
