import re
import numpy as np
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle
from tensorflow.keras.models import load_model
import fitz  # PyMuPDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from transformers import BertTokenizer, TFBertModel

# Load the tokenizer
with open('latest_tokenizer.pkl', 'rb') as f:
    tokenizer = pickle.load(f)

# Load the model
loaded_model = load_model('latest_model.keras')

# Load BERT tokenizer and model
bert_tokenizer = BertTokenizer.from_pretrained('distilbert-base-uncased')
bert_model = TFBertModel.from_pretrained('distilbert-base-uncased')

# Function to get BERT embeddings for a single word
def get_bert_embedding(word):
    inputs = bert_tokenizer(word, return_tensors='tf', padding=True, truncation=True, max_length=32)
    outputs = bert_model(inputs)
    return outputs.last_hidden_state[:, 0, :]  # Use the [CLS] token embedding

def deidentify_text(text):
    words = text.split()

    processed_words = []
    for word in words:
        # Tokenize the word
        MAX_SEQUENCE_LENGTH = 1
        sequence = tokenizer.texts_to_sequences([word])
        padded_sequence = pad_sequences(sequence, padding='post', maxlen=MAX_SEQUENCE_LENGTH)

        # Get BERT embedding for the word
        bert_embedding = get_bert_embedding(word).numpy()

        # Squeeze the extra dimension from BERT embeddings
        bert_embedding = np.squeeze(bert_embedding, axis=0)

        prediction = loaded_model.predict([np.array([bert_embedding]), padded_sequence])
        print(f"Word: {word}, Prediction: {prediction}")
        predicted_label = np.argmax(prediction, axis=-1)[0] 

        # Map the predicted label to PII or Non-PII
        if predicted_label == 1: 
            processed_words.append("[REDACTED]")
        else:
            processed_words.append(word)

    return " ".join(processed_words)

def extract_text_and_positions(pdf_path):
    doc = fitz.open(pdf_path)
    text_blocks = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("blocks") 
        for block in blocks:
            x0, y0, x1, y1, text, block_no, block_type = block
            text_blocks.append({
                "page_num": page_num,
                "text": text.strip(),
                "position": (x0, y0, x1, y1)
            })

    text_blocks.sort(key=lambda block: block["position"][1], reverse=False)
    return text_blocks

def create_deidentified_pdf(text_blocks, output_path):
    c = canvas.Canvas(output_path, pagesize=letter)

    for block in text_blocks:
        page_num = block["page_num"]
        text = block["text"]
        x0, y0, x1, y1 = block["position"]

        page_height = 792 
        y0_adjusted = page_height - y0 

        # Add text to the PDF at the same position
        c.drawString(x0, y0_adjusted, text)

    c.save()

def deidentify_pdf(input_path, output_path):
    try:
        print(f"Input PDF path: {input_path}")
        print(f"Output PDF path: {output_path}")

        text_blocks = extract_text_and_positions(input_path)
        print(f"Extracted {len(text_blocks)} text blocks.")

        for block in text_blocks:
            text = block["text"]
            # Check if the text contains a field delimiter (" - ")
            if " - " in text:
                field, value = text.split(" - ", 1) 
                # De-identify the value using the model
                deidentified_value = deidentify_text(value)
                block["text"] = f"{field} - {deidentified_value}"
            # else:
            #     # Use the model for other text (optional)
            #     block["text"] = deidentify_text(text)

        print("Text de-identified successfully.")

        create_deidentified_pdf(text_blocks, output_path)
        print(f"De-identified PDF saved to: {output_path}")

    except Exception as e:
        print(f"Error in deidentify_pdf: {e}")
        raise