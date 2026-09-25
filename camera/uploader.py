import os
import time
from datetime import datetime, timedelta, timezone
from supabase import create_client

BUCKET = "photos" # to be changed, name of the supabase storage bucket
SESSIONS_TABLE = "sessions" # to be changed, tentatively used for database table witth one row per photostrip?
LINK_TTL_SECONDS = 24 * 60 * 60 # to be changed, this determines how long download links stay valid for

# Amountof times to try each step before giving up
MAX_RETRIES = 3 

class Uploader:

    def __init__(self, client=None):
        if client is None:

            # Reads from the environment variables
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_KEY")

            if not url or not key:
                raise RuntimeError(
                    "Set SUPABASE_URL and SUPABASE_KEY environment variables first."
                )

            client = create_client(url, key)

        self.client = client

    def retry(self, action, func):

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return func()
            
            except Exception as e:
                # This logs which attempt failed and the cause of the failure
                print("{} failed ({}/{}): {}".format(action, attempt, MAX_RETRIES, e))

                if attempt == MAX_RETRIES:
                    raise

                time.sleep(2 ** attempt)

    # This function uploads one photo file
    def upload_file(self, local_path, remote_path):

        # This opens the JPEG on the RPI in read-binary mode
        with open(local_path, "rb") as f:
            # Reads the whole file into memory as bytes
            data = f.read()

        self.retry(
            "Upload of {}".format(remote_path),

            # The upload call, wrapped in a lambda so retry() can re-run it
            lambda: self.client.storage.from_(BUCKET).upload(
                remote_path, data, {"content-type": "image/jpeg", "upsert": "true"} # upsert = overwrite if it already exists, so retries won't return errors
            ),
        )

    # This function uploads all 4 photos of the confirmed strip
    def upload_session(self, session_id, photo_paths):

        # List of where each photo ends up in the bucket
        remote_paths = []

        for local_path in photo_paths:

            remote_path = "{}/{}".format(session_id, os.path.basename(local_path))

            # Uploads this photo
            self.upload_file(local_path, remote_path)

            # Remember its path in the bucket
            remote_paths.append(remote_path)

        # Create download links with retries 
        signed = self.retry(
            "Creating links",

            # This asks Supabase for temporary links, one link per photo and each valid for 24h ?
            lambda: self.client.storage.from_(BUCKET).create_signed_urls(
                remote_paths, LINK_TTL_SECONDS
            ),
        )

        # Pulls the link out of each result
        urls = [item.get("signedURL") or item.get("signedUrl") for item in signed]

        # Current time in UTC, which is the standard for databases 
        now = datetime.now(timezone.utc)

        # Time 24 hours from now
        expires_at = now + timedelta(seconds=LINK_TTL_SECONDS)

        # Only save a row if a table name is set
        if SESSIONS_TABLE:
            row = {
                "id": session_id, # Unique identifier for this photostrip
                "photo_paths": remote_paths, # Where the 4 photos are in the bucket
                "created_at": now.isoformat(), # Upload time as text
                "expires_at": expires_at.isoformat(),
            }

            # Saves the row with retries
            self.retry(
                "Saving session row",
                lambda: self.client.table(SESSIONS_TABLE).upsert(row).execute(), # upsert = insert or update if the id already exists
            )

        # Log success 
        print("Uploaded session {} ({} photos)".format(session_id, len(remote_paths)))

        # Returns results 
        return {
            "session_id": session_id,
            "paths": remote_paths,
            "urls": urls,
            "expires_at": expires_at.isoformat(),
        }