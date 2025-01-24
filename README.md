# Project Description

This project is a full-stack web application built with a FastAPI backend and a Next.js frontend, integrated with a PostgreSQL database. The application allows users to manage books and their respective authors, providing functionality for adding, editing, listing, filtering, and deleting books and authors. The project is containerized using Docker for easy deployment and setup.

---

## Features

### Backend (FastAPI)
- **Endpoints:**
  - `GET /books`: Retrieve a list of all books along with their authors. Optionally, you can provide an `author_id` as a query parameter to filter books by a specific author.
  - `POST /books`: Add a new book, including its title, year, and associated author. If the author does not exist, it will be created.
  - `PUT /books/{id}`: Update details of a specific book, including its title, year, and associated author. If the author does not exist, it will be created or updated.
  - `DELETE /books/{id}`: Delete a specific book by its ID.
- **Database Design:**
  - **Authors Table:**
    - `id` (Primary Key, Integer)
    - `name` (String)
  - **Books Table:**
    - `id` (Primary Key, Integer)
    - `title` (String)
    - `year` (Integer)
    - `status` (Enum: [PUBLISHED, DRAFT])
    - `author_id` (Foreign Key referencing Authors Table)
- **Testing:**
  - Pytest for unit tests.
  - Pydantic for data validation.

### Frontend (Next.js)
- **Features:**
  - Form to add/edit books, including fields for title, year, and author selection (populated from the authors list).
  - Support for creating or editing authors directly from the form.
  - List view displaying all books with options to edit or delete each entry.
  - Filter functionality to view books by a specific author.
  - Validations for all inputs.
- **Testing:**
  - Jest for unit tests.

### Docker
- Dockerfiles for both FastAPI and Next.js applications.
- A `docker-compose.yml` file that sets up:
  - FastAPI backend.
  - Next.js frontend.
  - PostgreSQL database service.

---

## Setup Instructions

### Prerequisites
- Install Docker and Docker Compose. Use Docker Desktop for ease of use.
- Install Python (3.8 or later) and Node.js (16.x or later) for development or testing outside Docker.

### Running the Application
1. Clone the repository from GitHub:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```
2. Start Docker Compose:
   ```bash
   docker compose up
   ```
3. Access the application:
   - API Documentation: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
   - Frontend: [http://localhost:3000](http://localhost:3000)

### Running Backend Tests
1. Create a virtual environment:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   python -m pip install -r tests/requirements.txt
   ```
3. Run tests:
   ```bash
   pytest
   ```

### Running Frontend Tests
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run tests:
   ```bash
   npm test
   ```

---

## Additional Notes
- Make sure Docker, Python (3.8 or later), and Node.js (16.x or later) are installed on your system.
- For better development experience, it's recommended to use Visual Studio Code (VSCode) with appropriate extensions for Python and JavaScript.
