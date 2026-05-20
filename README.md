# 📊 Financial Document Management API

An AI-powered REST API for managing and semantically searching financial documents using RAG (Retrieval Augmented Generation) pipeline.

---

## 🎯 What This Project Does

Companies deal with thousands of financial documents — invoices, reports, contracts. Finding specific information manually takes hours.

This system solves that by allowing users to:
- Upload financial PDFs securely
- Search them using **natural language questions**
- Get AI-powered answers with exact relevant paragraphs in seconds

Instead of keyword search, the AI **understands meaning**. Search *"company debt problems"* and it finds documents about *"high leverage ratio"* or *"financial risk"* automatically.

---

## 🏗️ Architecture

```
Upload PDF
    ↓
Text Extraction (pdfplumber)
    ↓
Semantic Chunking
    ↓
Embeddings (Sentence Transformers)
    ↓
Vector Storage (FAISS)

── Search ──────────────────

User Query
    ↓
Embed Query
    ↓
FAISS Search → Top 20 Results
    ↓
Cross-Encoder Reranking
    ↓
Top 5 Most Relevant Results
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | FastAPI |
| Database | SQLite + SQLAlchemy |
| Authentication | JWT + bcrypt |
| Vector Database | FAISS |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Reranking | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| PDF Parsing | pdfplumber |

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/financial-rag-api.git
cd financial-rag-api
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate.bat

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup environment
```bash
cp .env.example .env
```

### 5. Run the API
```bash
uvicorn main:app --reload
```

### 6. Open Swagger UI
```
http://localhost:8000/docs
```

---

## 🔑 Default Login

| Username | Password | Role |
|---|---|---|
| admin | Admin@1234 | Admin (full access) |

---

## 📋 API Endpoints

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | /auth/register | Register new user |
| POST | /auth/login | Login and get JWT token |

### Documents
| Method | Endpoint | Description |
|---|---|---|
| POST | /documents/upload | Upload a PDF document |
| GET | /documents | List all documents |
| GET | /documents/{id} | Get document details |
| DELETE | /documents/{id} | Delete a document |
| GET | /documents/search | Search by metadata |

### Roles & Permissions
| Method | Endpoint | Description |
|---|---|---|
| POST | /roles/create | Create a role |
| POST | /users/assign-role | Assign role to user |
| GET | /users/{id}/roles | Get user roles |
| GET | /users/{id}/permissions | Get user permissions |

### RAG - AI Search
| Method | Endpoint | Description |
|---|---|---|
| POST | /rag/index-document | Index PDF into vector DB |
| POST | /rag/search | Semantic search |
| GET | /rag/context/{id} | Get document chunks |
| DELETE | /rag/remove-document/{id} | Remove embeddings |

---

## 👥 Role Based Access Control

| Role | Permissions |
|---|---|
| Admin | Full access |
| Analyst | Upload, edit, view |
| Auditor | View only |
| Client | View company documents |

---

## 💡 How to Use

### Step 1 — Login
```json
POST /auth/login
{
  "username": "admin",
  "password": "Admin@1234"
}
```

### Step 2 — Upload a Document
```
POST /documents/upload
Form data:
  - file: your_document.pdf
  - title: Q1 Financial Report
  - company_name: Acme Corp
  - document_type: report
```

### Step 3 — Index for AI Search
```
POST /rag/index-document?document_id=your_document_id
```

### Step 4 — Search with Natural Language
```json
POST /rag/search
{
  "query": "what are the financial risks mentioned in the report?"
}
```

### Response
```json
{
  "query": "what are the financial risks mentioned in the report?",
  "results": [
    {
      "document_id": "abc-123",
      "title": "Q1 Financial Report",
      "company_name": "Acme Corp",
      "document_type": "report",
      "chunk_text": "The company faces significant financial risk due to high debt ratio...",
      "score": 8.912
    }
  ]
}
```

---

## 📁 Project Structure

```
financial_rag/
├── main.py                  # App entry point
├── config.py                # Settings
├── database.py              # SQLAlchemy setup
├── requirements.txt         # Dependencies
├── .env.example             # Environment template
├── models/
│   ├── user.py              # User and Role models
│   └── document.py          # Document model
├── schemas/
│   ├── auth.py              # Auth schemas
│   ├── document.py          # Document schemas
│   ├── role.py              # Role schemas
│   └── rag.py               # RAG schemas
├── routers/
│   ├── auth.py              # Auth endpoints
│   ├── documents.py         # Document endpoints
│   ├── roles.py             # Role endpoints
│   └── rag.py               # RAG endpoints
├── services/
│   ├── auth_service.py      # Auth logic
│   ├── document_service.py  # Document logic
│   ├── role_service.py      # Role logic
│   └── rag_service.py       # RAG pipeline
└── utils/
    └── security.py          # JWT and permissions
```

---

## 🌟 Key Features

- ✅ JWT Authentication and Authorization
- ✅ Role Based Access Control (4 roles)
- ✅ PDF upload and management
- ✅ Complete RAG pipeline
- ✅ Semantic search (meaning based, not keyword)
- ✅ Cross-encoder reranking for better results
- ✅ Local vector storage with FAISS
- ✅ Interactive API docs at /docs

---

## 👨‍💻 Author

Made with ❤️ for AI/ML Assignment

---

## 📄 License

MIT License
