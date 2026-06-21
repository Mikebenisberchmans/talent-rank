# setup.py
# Run once before the competition to pre-download the cross-encoder model.
# This ensures the ranking run has zero network calls.

from pipeline.semantic_scorer import download_model_if_needed
download_model_if_needed()
print("Setup complete. You can now run main.py offline.")
