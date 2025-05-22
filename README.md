# ClearAI Backend

A FastAPI backend for processing Thai images, analyzing with LLM, and returning Thai JSON responses.

## System Flow

1. Frontend uploads Thai image
2. Backend prepares and encodes the image
3. Image is sent directly to LLM (GPT-4o) which processes the Thai text and generates English reasoning with structured JSON answer
4. Backend translates the structured answer from English to Thai
5. Final Thai JSON is returned to the frontend

## Setup

### Prerequisites

- Python 3.8+
- OpenAI API key with access to GPT-4o

### Installation

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/clear-ai-backend.git
   cd clear-ai-backend
   ```

2. Create a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### Running the Server

Start the development server:

```
python main.py
```

Or using uvicorn directly:

```
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

## API Endpoints

### Upload Image

**Endpoint**: `POST /api/upload`

**Request**:

- Form data with an image file

**Response**:

```json
{
  "success": true,
  "message": "Image processed successfully",
  "data": {
    "reasoning": "English reasoning about the Thai text...",
    "structured_answer": {
      "key1": "Thai translated value1",
      "key2": "Thai translated value2"
    }
  }
}
```

## Documentation

API documentation is automatically generated and available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
