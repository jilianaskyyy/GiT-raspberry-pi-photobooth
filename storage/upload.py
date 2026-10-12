from db import supabase

BUCKET = "Photos"

def save_photo(session_id, photo_number, file_path):
    path = f"{session_id}/{photo_number}.jpg"
    with open(file_path, "rb") as f:
        supabase.storage.from_(BUCKET).upload(
            path, f, {"content-type": "image/jpeg"}
        )
    photo_url = supabase.storage.from_(BUCKET).get_public_url(path)
    supabase.table("Photo_data").insert({
        "session_id": session_id,
        "photo_url": photo_url
    }).execute()
    return photo_url