import os
import shutil

def clear_uploads():
    uploads_dir = "/shared/uploads"
    try:
        shutil.rmtree(uploads_dir)
        os.makedirs(uploads_dir)
        print("Uploads directory cleared.")
    except FileNotFoundError:
        print("Uploads directory not found.")
    except Exception as e:
        print(f"Error clearing uploads directory: {str(e)}")

def clear_database():
    db_file = "/shared/sqlite/shared_db.sqlite"
    try:
        os.remove(db_file)
        print("Database file deleted.")
    except FileNotFoundError:
        print("Database file not found.")
    except Exception as e:
        print(f"Error deleting database file: {str(e)}")

if __name__ == "__main__":
    clear_uploads()
    clear_database()