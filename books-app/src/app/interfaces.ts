import { StatusEnum } from "./consts";

export type Status = keyof typeof StatusEnum;

export interface Author {
  id: number;
  name: string;
}

export interface Book {
  id: number;
  title: string;
  year: number;
  status: Status;
  author: Author;
}

export interface BookPayload {
  id: number | undefined;
  title: string;
  year: number;
  status: Status;
  author_id: number;
  author_name: string;
}
