import { BookPayload } from "@/app/types/interfaces";
import React, { useState } from "react";
import CreateBookButton from "./CreateBookButton";
import SaveBook from "./SaveBook";

interface CreateBookProps {
  sendSave: (book: BookPayload) => void;
}

const CreateBook: React.FC<CreateBookProps> = ({ sendSave }) => {
  const [showCreate, setShowCreate] = useState(false);

  const openSaveForm = () => setShowCreate(true);
  const closeSaveForm = () => setShowCreate(false);

  if (showCreate)
    return (
      <SaveBook book={null} handleClose={closeSaveForm} sendSave={sendSave} />
    );
  else return <CreateBookButton handleClick={openSaveForm} />;
};

export default CreateBook;
