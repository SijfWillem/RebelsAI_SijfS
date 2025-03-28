import sys
print(f"Python version: {sys.version}")

try:
    import fastapi
    print("✓ FastAPI imported successfully")
except ImportError as e:
    print("✗ FastAPI import failed:", e)

try:
    import uvicorn
    print("✓ Uvicorn imported successfully")
except ImportError as e:
    print("✗ Uvicorn import failed:", e)

try:
    import flask
    print("✓ Flask imported successfully")
except ImportError as e:
    print("✗ Flask import failed:", e)

try:
    import spacy
    print("✓ spaCy imported successfully")
except ImportError as e:
    print("✗ spaCy import failed:", e)

try:
    import textblob
    print("✓ TextBlob imported successfully")
except ImportError as e:
    print("✗ TextBlob import failed:", e) 