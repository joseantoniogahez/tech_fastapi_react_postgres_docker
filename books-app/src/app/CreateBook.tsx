import React, { useState } from "react";
import CreateButton from "./CreateButton";
import SaveBook from "./SaveBook";
import { BookPayload } from "./interfaces";

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
  else return <CreateButton handleClick={openSaveForm} />;
};

export default CreateBook;
