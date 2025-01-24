import { BookPayload } from "@/app/types/interfaces";
import React, { useState } from "react";
import CreateBookButton from "./CreateBookButton";
import SaveBookForm from "./SaveBookForm";

interface CreateBookProps {
  sendSave: (book: BookPayload) => void;
}

const CreateBook: React.FC<CreateBookProps> = ({ sendSave }) => {
  const [showCreate, setShowCreate] = useState(false);

  const openSaveForm = () => setShowCreate(true);
  const closeSaveForm = () => setShowCreate(false);

  if (showCreate)
    return (
      <SaveBookForm
        book={null}
        handleClose={closeSaveForm}
        sendSave={sendSave}
      />
    );
  else return <CreateBookButton handleClick={openSaveForm} />;
};

export default CreateBook;
