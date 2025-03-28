# Document Analysis Dashboard

A modern web application for analyzing and managing document collections with advanced classification and metadata extraction capabilities.

## Features

- **Document Upload**: Drag-and-drop interface for uploading folders and documents
- **Document Analysis**: Automatic extraction of metadata and content analysis
- **Classification**: AI-powered document classification
- **Interactive UI**: Modern, responsive interface with real-time updates
- **Database Storage**: Persistent storage of document metadata and analysis results
- **Folder Structure**: Hierarchical organization with expandable/collapsible folders

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Flask with TailwindCSS
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI/ML**: OpenAI API for document classification
- **File Processing**: python-magic, python-docx, PyPDF2

## Prerequisites

- Python 3.8+
- PostgreSQL 13+
- Node.js 14+ (for frontend assets)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/SijfWillem/RebelsAI_Sijf.git
cd RebelsAI_Sijf
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
# Create PostgreSQL database
createdb document_analysis

# Run database migrations
alembic upgrade head
```

5. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

Create a `.env` file with the following variables:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/document_analysis
MISTRAL_API_KEY=your_mistral_api_key
```

## Project Structure

```
RebelsAI_Sijf/
├── app/
│   ├── models/              # Data models and database schemas
│   ├── services/            # Business logic and database operations
│   └── api/                 # API routes and endpoints
├── frontend/
│   ├── app.py              # Flask frontend server
│   └── templates/          # HTML templates
├── migrations/             # Database migrations
├── requirements.txt        # Python dependencies
└── README.md              # Project documentation
```

## Database Schema

The application uses three main tables:

1. **documents**
   - Stores document metadata and content
   - Tracks file information and processing status
   - Links to parent folders

2. **folders**
   - Manages folder hierarchy
   - Stores folder metadata
   - Supports nested folder structures

3. **classifications**
   - Stores document classification results
   - Links to parent documents
   - Includes confidence scores

## API Endpoints

- `POST /api/upload-folder`: Upload a folder for analysis
- `GET /api/folder-insights`: Get comprehensive folder analysis
- `GET /api/documents`: Get paginated document list
- `GET /api/documents/{id}`: Get specific document details
- `DELETE /api/documents/{id}`: Delete a document

## Usage

1. Start the backend server:
```bash
uvicorn app.main:app --reload
```

2. Start the frontend server:
```bash
python frontend/app.py
```

3. Open your browser and navigate to `http://localhost:5000`

4. Upload a folder to begin analysis

## Database Management

### Migrations

To create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

To apply migrations:
```bash
alembic upgrade head
```

To rollback migrations:
```bash
alembic downgrade -1
```

### Backup and Restore

To backup the database:
```bash
pg_dump -U postgres document_analysis > backup.sql
```

To restore from backup:
```bash
psql -U postgres document_analysis < backup.sql
```

## Error Handling

The application includes comprehensive error handling for:
- Database connection issues
- File upload problems
- Invalid file types
- Processing errors
- Network connectivity problems

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- FastAPI for the backend framework
- Flask for the frontend server
- SQLAlchemy for database ORM
- PostgreSQL for the database
- Tailwind CSS for styling
