# setup.py
# Run ONCE before the competition to download and save the cross-encoder
# model into the project's models/ folder.
#
# After this runs, the entire ranking pipeline is offline — no network needed.
#
# Usage:
#   python setup.py

import os
from sentence_transformers import CrossEncoder

MODEL_NAME  = "cross-encoder/ms-marco-MiniLM-L-6-v2"
MODEL_DIR   = os.path.join(os.path.dirname(__file__), "models", "cross-encoder")

def main():
    print(f"Downloading model: {MODEL_NAME}")
    print(f"Saving to       : {MODEL_DIR}")
    print()

    os.makedirs(MODEL_DIR, exist_ok=True)
    model = CrossEncoder(MODEL_NAME)
    model.save(MODEL_DIR)

    print()
    print("Model saved. Contents of models/cross-encoder/:")
    for f in sorted(os.listdir(MODEL_DIR)):
        size = os.path.getsize(os.path.join(MODEL_DIR, f))
        print(f"  {f:<40} {size/1024:.1f} KB")

    print()
    print("Setup complete. You can now run main.py with no internet connection.")

if __name__ == "__main__":
    main()
