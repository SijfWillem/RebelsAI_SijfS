# Document Analysis Dashboard

A modern web application for analyzing and managing document collections with AI-powered classification capabilities.

## Features

- **Document Upload**: Drag-and-drop interface for uploading folders and documents
- **Document Analysis**: Automatic extraction of metadata and content analysis
- **AI Classification**: Mistral AI-powered document classification
- **Interactive UI**: Modern, responsive interface with real-time updates
- **Caching**: Efficient caching of classification results
- **Folder Structure**: Hierarchical organization with expandable/collapsible folders

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Flask with TailwindCSS
- **AI/ML**: Mistral AI API for document classification
- **File Processing**: python-magic, python-docx, PyPDF2
- **Caching**: Local file-based caching system

## Prerequisites

- Python 3.8+
- Mistral AI API key (get one at https://mistral.ai/)

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/SijfWillem/RebelsAI_SijfS.git
cd RebelsAI_SijfS
```

2. Make the start script executable:
```bash
chmod +x start.sh
```

3. Run the application:
```bash
./start.sh
```

The script will:
- Create a virtual environment if it doesn't exist
- Install all required dependencies
- Create necessary directories
- Check for the .env file and create it if missing
- Start both the backend and frontend servers

4. Open your browser and navigate to `http://localhost:5001`

## Manual Installation

If you prefer to set up the environment manually:

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install backend dependencies:
```bash
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
pip install -r frontend/requirements.txt
```

4. Create necessary directories:
```bash
mkdir -p backend/cache
mkdir -p backend/uploads
mkdir -p frontend/temp_uploads
```

5. Create a `.env` file with your Mistral AI API key:
```bash
echo "MISTRAL_API_KEY=your_mistral_api_key" > .env
```

6. Start the backend server:
```bash
cd backend
uvicorn app:app --reload --port 8000
```

7. In a new terminal, start the frontend server:
```bash
cd frontend
python app.py
```

## Project Structure

```
RebelsAI_SijfS/
├── backend/
│   ├── app.py              # FastAPI backend server
│   ├── cache/              # Classification cache
│   └── uploads/            # Temporary file uploads
├── frontend/
│   ├── app.py              # Flask frontend server
│   ├── templates/          # HTML templates
│   └── temp_uploads/       # Temporary uploads
├── requirements.txt        # Backend dependencies
├── frontend/requirements.txt # Frontend dependencies
├── start.sh               # Start script
├── .env                   # Environment variables
└── README.md              # Project documentation
```

## API Endpoints

### Backend (FastAPI)

- `POST /api/analyze-folder`: Upload a folder for analysis
- `GET /api/folder-insights`: Get comprehensive folder analysis
- `GET /api/documents`: Get list of documents in a folder

### Frontend (Flask)

- `GET /`: Main dashboard
- `POST /api/upload-folder`: Handle folder uploads
- `GET /api/folder-insights`: Get folder insights
- `GET /api/documents`: Get document list
- `GET /health`: Health check endpoint

## Configuration

The application can be configured through environment variables in the `.env` file:

```env
MISTRAL_API_KEY=your_mistral_api_key
BACKEND_URL=http://localhost:8000  # Optional, defaults to localhost:8000
```

## Error Handling

The application includes comprehensive error handling for:
- File upload problems
- Invalid file types
- Processing errors
- Network connectivity problems
- API rate limiting
- File size limits

## Caching

The application implements a file-based caching system for document classifications to:
- Reduce API calls to Mistral AI
- Improve response times
- Handle rate limiting gracefully

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
- Mistral AI for document classification
- Tailwind CSS for styling
