
```
fastapi_chat
├─ .env
├─ api
│  └─ v1
│     ├─ endpoints
│     │  ├─ documents.py
│     │  ├─ messages.py
│     │  ├─ sessions.py
│     │  ├─ users.py
│     │  └─ __pycache__/
│     └─ schemas
│        ├─ document.py
│        ├─ message.py
│        ├─ session.py
│        ├─ user.py
│        └─ __pycache__/
├─ config
│  ├─ settings.py
│  └─ __pycache__/
├─ core
│  ├─ database.py
│  └─ __pycache__/
├─ main.py
├─ models
│  └─ models.py
├─ README.md
├─ requirements.txt
├─ services
│  ├─ agent_service.py
│  ├─ document_service.py
│  ├─ vector_store_service.py
│  └─ __pycache__/
└─ __pycache__/

```
---
Database vector, sudah di connect online, tinggal setup database chat memory di postgresql local,

```
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE
);

CREATE TABLE messages (
    message_id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(session_id),
    sender VARCHAR(50) NOT NULL,
    message_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---
## Key Components

### **1. `main.py`**

* Initializes the FastAPI app.
* Includes all versioned API routers (from `api/v1/endpoints`).
* Configures middleware, error handlers, etc.

### **2. `config/settings.py`**

* Loads environment variables with `python-dotenv`.
* Provides centralized access to settings (e.g., DB URL, API keys).

### **3. `core/database.py`**

* Sets up the SQLAlchemy engine and session.
* Manages database initialization.

### **4. `api/v1/endpoints/`**

* Contains REST API routes for each entity:

  * `users.py`: create and manage users
  * `sessions.py`: manage chat sessions
  * `messages.py`: handle message sending/retrieval
  * `documents.py`: handle document uploads and retrieval

### **5. `api/v1/schemas/`**

* Defines **Pydantic models** for request/response validation.

### **6. `models/models.py`**

* Defines the SQLAlchemy ORM models corresponding to database tables.

### **7. `services/`**

* Handles the main business logic:

  * `agent_service.py`: integrates with AI/LLM agents.
  * `document_service.py`: manages document storage and retrieval.
  * `vector_store_service.py`: connects to a vector database (e.g., Pinecone, FAISS).
