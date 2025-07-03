"""
Notes Backend API using FastAPI

This API allows users to create, read, update, and delete personal notes.
Persistent storage is implemented using a JSON file (`data.json`) for simplicity.

Features:
- View all notes
- View a single note by ID
- Create a new note
- Edit an existing note
- Delete a note

OpenAPI documentation is enabled at `/docs`.
"""

from fastapi import FastAPI, HTTPException, Path, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
import json
import os
from datetime import datetime

app = FastAPI(
    title="Notes Backend API",
    description="RESTful API for notes operations: create, read, update, and delete notes.",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "notes",
            "description": "Operations with Notes (CRUD API)"
        }
    ],
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DATA_DIR, "data.json")

def _load_notes():
    """Load notes from the JSON data file."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
    with open(DATA_FILE, "r") as f:
        try:
            notes = json.load(f)
        except json.JSONDecodeError:
            notes = []
    return notes

def _save_notes(notes):
    """Save notes to the JSON data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(notes, f, indent=2)

# ------------------- Models/Schemas -------------------

# PUBLIC_INTERFACE
class NoteBase(BaseModel):
    """Base schema for note creation/updating."""
    title: str = Field(..., description="Title of the note", min_length=1)
    content: str = Field(..., description="Content of the note", min_length=1)

# PUBLIC_INTERFACE
class NoteCreate(NoteBase):
    """Schema for creating a note."""
    pass

# PUBLIC_INTERFACE
class NoteUpdate(BaseModel):
    """Schema for updating a note."""
    title: Optional[str] = Field(None, description="Title of the note", min_length=1)
    content: Optional[str] = Field(None, description="Content of the note", min_length=1)

# PUBLIC_INTERFACE
class Note(NoteBase):
    """Schema for note returned in responses."""
    id: str = Field(..., description="Unique identifier for the note")
    created_at: str = Field(..., description="Creation time (ISO 8601)")
    updated_at: str = Field(..., description="Last update time (ISO 8601)")

# PUBLIC_INTERFACE
class MessageResponse(BaseModel):
    """Response message schema."""
    message: str

# --------------- Utility and Data Operations ------------

def _get_note_by_id(note_id: str, notes: list) -> Optional[dict]:
    """Fetch a note dict by its ID."""
    for note in notes:
        if note['id'] == note_id:
            return note
    return None

# ------------------ API Routes ------------------

@app.get("/", tags=["health"], summary="Health check", description="Health check endpoint to verify that the API is running.")
def health_check():
    """API health check endpoint."""
    return {"message": "Healthy"}

# PUBLIC_INTERFACE
@app.get(
    "/notes",
    response_model=List[Note],
    summary="Get all notes",
    description="Returns a list of all notes.",
    tags=["notes"]
)
def list_notes():
    """Get all notes."""
    notes = _load_notes()
    return notes

# PUBLIC_INTERFACE
@app.get(
    "/notes/{note_id}",
    response_model=Note,
    summary="Get a single note",
    description="Retrieve a note by its ID.",
    responses={
        404: {"model": MessageResponse, "description": "Note not found."}
    },
    tags=["notes"],
)
def get_note(note_id: str = Path(..., description="ID of the note")):
    """Fetch a note by its ID."""
    notes = _load_notes()
    note = _get_note_by_id(note_id, notes)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")
    return note

# PUBLIC_INTERFACE
@app.post(
    "/notes",
    response_model=Note,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new note",
    description="Create and return a new note.",
    tags=["notes"],
)
def create_note(note_create: NoteCreate):
    """Create a new note."""
    notes = _load_notes()
    note_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    new_note = {
        "id": note_id,
        "title": note_create.title,
        "content": note_create.content,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    notes.append(new_note)
    _save_notes(notes)
    return new_note

# PUBLIC_INTERFACE
@app.put(
    "/notes/{note_id}",
    response_model=Note,
    summary="Update an existing note",
    description="Update the title and/or content of an existing note.",
    responses={
        404: {"model": MessageResponse, "description": "Note not found."}
    },
    tags=["notes"],
)
def update_note(
    note_id: str = Path(..., description="ID of the note to update"),
    note_update: NoteUpdate = ...
):
    """Update an existing note."""
    notes = _load_notes()
    note = _get_note_by_id(note_id, notes)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")

    updated = False
    now = datetime.utcnow().isoformat()
    if note_update.title is not None:
        note['title'] = note_update.title
        updated = True
    if note_update.content is not None:
        note['content'] = note_update.content
        updated = True

    if updated:
        note['updated_at'] = now
        _save_notes(notes)
    return note

# PUBLIC_INTERFACE
@app.delete(
    "/notes/{note_id}",
    response_model=MessageResponse,
    summary="Delete a note",
    description="Delete a note by its ID.",
    responses={
        404: {"model": MessageResponse, "description": "Note not found."},
        200: {"model": MessageResponse, "description": "Note deleted successfully."}
    },
    tags=["notes"],
)
def delete_note(note_id: str = Path(..., description="ID of the note to delete")):
    """Delete a note."""
    notes = _load_notes()
    note = _get_note_by_id(note_id, notes)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")
    notes = [n for n in notes if n["id"] != note_id]
    _save_notes(notes)
    return MessageResponse(message="Note deleted successfully.")

# ---------- OpenAPI Usage Help (Docs Route) ----------

@app.get(
    "/openapi_usage_help",
    summary="OpenAPI/WebSocket usage help",
    description="Provides information about usage of OpenAPI endpoints.",
)
def openapi_usage_help():
    """
    Application uses RESTful endpoints for all note interactions.
    - Main endpoints:
        - GET /notes: List all notes
        - GET /notes/{note_id}: Get note by ID
        - POST /notes: Create note
        - PUT /notes/{note_id}: Update note
        - DELETE /notes/{note_id}: Delete note

    OpenAPI/Swagger docs at `/docs`.
    """
    return {
        "message": "See `/docs` for OpenAPI documentation. No websocket endpoints are available for this API."
    }
