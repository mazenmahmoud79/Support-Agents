# AI Customer Service System

Production-ready AI customer service chatbot with RAG (Retrieval Augmented Generation), multi-tenancy, and dynamic knowledge base management.

## 🎯 Quick Demo Access

This project uses a **simplified demo authentication system**. You can instantly access the system using any of the 100 pre-generated demo IDs:

**Demo ID Format**: `DEMO-XXXXXX` (e.g., `DEMO-A1B2C3`)

📋 **See [DEMO_IDS.md](DEMO_IDS.md) for the complete list of all 100 demo IDs**

### Try It Now
1. Start the application (see [Quick Start](#quick-start) below)
2. Go to http://localhost
3. Enter any demo ID from [DEMO_IDS.md](DEMO_IDS.md)
4. Click "Access Demo"
5. Start chatting!

📖 **For complete authentication documentation, see [DEMO_AUTHENTICATION.md](DEMO_AUTHENTICATION.md)**

## 🚀 Features

- **RAG-Powered Chatbot**: Groq LLM with semantic search using Qdrant vector database
- **Multi-Tenant Architecture**: Isolated data for multiple companies/clients
- **Dynamic Knowledge Base**: Upload PDF, DOCX, TXT, CSV files with automatic processing
- **Full CRUD Operations**: Manage documents with create, read, update, delete
- **Streaming Responses**: Real-time chat with Server-Sent Events
- **Source Attribution**: Track which documents were used to generate responses
- **Admin Dashboard**: Analytics, document management, and system health monitoring
- **Modern UI**: React + TypeScript with dark theme and responsive design

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   React     │────▶│   FastAPI    │────▶│   Qdrant    │
│  Frontend   │     │   Backend    │     │   Vector    │
│             │     │              │     │     DB      │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ├──────▶ PostgreSQL (Metadata)
                           ├──────▶ Groq API (LLM)
                           └──────▶ Redis (Caching)
```

## 📦 Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (metadata), Qdrant (vectors)
- **LLM**: Groq API (llama-3.3-70b-versatile)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Caching**: Redis (optional)

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **State Management**: Zustand
- **Styling**: Custom CSS with CSS variables
- **HTTP Client**: Axios

### Infrastructure
- **Containerization**: Docker, Docker Compose
- **Web Server**: Nginx (production)

## 🛠️ Setup & Installation

### Prerequisites
- Docker and Docker Compose
- Groq API key (get from https://console.groq.com)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Support_Agent
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` file**
   - Add your Groq API key
   - Change default passwords
   - Update SECRET_KEY to a random string

4. **Start all services**
   ```bash
   docker-compose up --build
   ```

5. **Access the application**
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Qdrant Dashboard: http://localhost:6333/dashboard

### First Time Setup

1. **Login with demo ID**
   - Navigate to http://localhost
   - Enter any demo ID from [DEMO_IDS.md](DEMO_IDS.md) (e.g., `DEMO-A1B2C3`)
   - Click "Access Demo"
   - You're now logged in as the "Mohr Software Solutions" demo tenant

2. **Upload documents**
   - Login with your API key
   - Go to "Upload" page
   - Drag and drop PDF/DOCX/TXT/CSV files
   - Wait for processing to complete

3. **Start chatting**
   - Go to "Chat" page
   - Ask questions about your uploaded documents
   - View source attributions for answers

## 📂 Project Structure

```
Support_Agent/
├── backend/
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Security, logging
│   │   ├── db/             # Database config
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic
│   │   ├── config.py       # Settings
│   │   └── main.py         # App entry point
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── hooks/          # Custom hooks
│   │   ├── types/          # TypeScript types
│   │   └── styles/         # Global styles
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
└── .env.example
```

## 🔑 API Endpoints

### Authentication
- `POST /api/auth/login` - Login with demo ID

### Documents
- `POST /api/documents/upload` - Upload files
- `GET /api/documents` - List documents
- `GET /api/documents/{id}` - Get document details
- `PUT /api/documents/{id}` - Update document
- `DELETE /api/documents/{id}` - Delete document
- `POST /api/documents/batch-delete` - Bulk delete

### Chat
- `POST /api/chat` - Send message (with sources)
- `POST /api/chat/stream` - Send message (streaming)
- `GET /api/chat/history/{session_id}` - Get conversation history
- `DELETE /api/chat/history/{session_id}` - Clear history

### Admin
- `GET /api/admin/analytics` - Get usage analytics
- `GET /api/admin/documents/stats` - Document statistics
- `GET /api/admin/health` - System health check

## 🔧 Configuration

Key environment variables in `.env`:

```env
# Required
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=your_secret_key_here
POSTGRES_PASSWORD=your_secure_password

# Optional
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
SIMILARITY_THRESHOLD=0.7
TOP_K_RESULTS=5
```

## 🧪 Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

## 📊 How It Works

1. **Document Upload**: Files are parsed, chunked (1000 tokens with 200 overlap), and converted to embeddings
2. **Vector Storage**: Embeddings stored in Qdrant with metadata in PostgreSQL
3. **Query**: User question → embedding → semantic search in Qdrant → retrieve top-K chunks
4. **Generation**: Retrieved context + question → Groq LLM → streaming response
5. **Attribution**: Sources tracked and displayed with relevance scores

## 🔐 Security Features

- API key authentication
- Multi-tenant data isolation
- Rate limiting
- Input sanitization
- CORS protection
- Security headers in Nginx

## 📈 Scalability

- Async processing for uploads
- Connection pooling (PostgreSQL)
- Vector database optimized for similarity search
- Horizontal scaling ready
- CDN-friendly static assets

## 🐛 Troubleshooting

### Backend won't start
- Check Groq API key is valid
- Verify database connection string
- Ensure all required env vars are set

### Frontend can't connect to backend
- Check backend is running on port 8000
- Verify CORS settings in backend
- Check browser console for errors

### Uploads fail
- Check file size (max 10MB)
- Verify file format (PDF, DOCX, TXT, CSV)
- Check backend logs for processing errors

### Chat responses are slow
- Groq API may be rate limited
- Check network connectivity
- Verify Qdrant is running

## 📝 License

This project is provided as-is for demonstration purposes.

## 🆘 Support

For issues and questions:
1. Check the API documentation at http://localhost:8000/docs
2. Review backend logs: `docker-compose logs backend`
3. Check Qdrant dashboard: http://localhost:6333/dashboard
4. Inspect browser console for frontend errors

## 🎯 Next Steps

- Add user authentication (OAuth, JWT)
- Implement conversation memory
- Add file versioning
- Create API rate limiting dashboard
- Add support for more file formats
- Implement conversation export
- Add multi-language support
