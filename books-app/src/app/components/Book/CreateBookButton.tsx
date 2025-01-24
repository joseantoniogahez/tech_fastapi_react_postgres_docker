import React from "react";

interface CreateButtonProps {
  handleClick: () => void;
}

const CreateBookButton: React.FC<CreateButtonProps> = ({ handleClick }) => {
  return (
    <div className="fixed bottom-4 right-4">
      <button
        onClick={handleClick}
        className="bg-blue-500 text-white rounded-full p-4 shadow-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300"
        aria-label="Create"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 4v16m8-8H4"
          />
        </svg>
      </button>
    </div>
  );
};

export default CreateBookButton;
