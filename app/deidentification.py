import re
import numpy as np
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle
from tensorflow.keras.models import load_model
import fitz  
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from transformers import BertTokenizer, TFBertModel

with open('latest_tokenizer.pkl', 'rb') as f:
    tokenizer = pickle.load(f)

loaded_model = load_model('latest_model.keras')

bert_tokenizer = BertTokenizer.from_pretrained('distilbert-base-uncased')
bert_model = TFBertModel.from_pretrained('distilbert-base-uncased')

def get_bert_embedding(word):
    inputs = bert_tokenizer(word, return_tensors='tf', padding=True, truncation=True, max_length=32)
    outputs = bert_model(inputs)
    return outputs.last_hidden_state[:, 0, :]

def deidentify_text(text):
    words = text.split()

    processed_words = []
    for word in words:
        MAX_SEQUENCE_LENGTH = 1
        sequence = tokenizer.texts_to_sequences([word])
        padded_sequence = pad_sequences(sequence, padding='post', maxlen=MAX_SEQUENCE_LENGTH)
        bert_embedding = get_bert_embedding(word).numpy()
        bert_embedding = np.squeeze(bert_embedding, axis=0)

        prediction = loaded_model.predict([np.array([bert_embedding]), padded_sequence])
        print(f"Word: {word}, Prediction: {prediction}")
        predicted_label = np.argmax(prediction, axis=-1)[0] 

        if predicted_label == 1: 
            processed_words.append("[REDACTED]")
        else:
            processed_words.append(word)

    return " ".join(processed_words)

def extract_text_and_positions(pdf_path):
    doc = fitz.open(pdf_path)
    text_blocks = []
    
    # Use detailed extraction to get font and color info.
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        bbox = span.get("bbox", (0, 0, 0, 0))
                        font = span.get("font", "Helvetica")
                        size = span.get("size", 12)
                        
                        color_int = span.get("color", 0)
                        r = ((color_int >> 16) & 0xFF) / 255.0
                        g = ((color_int >> 8) & 0xFF) / 255.0
                        b = (color_int & 0xFF) / 255.0
                        rgb_color = (r, g, b)
                        
                        text_blocks.append({
                            "page_num": page_num,
                            "text": text,
                            "position": bbox,
                            "font": font,
                            "size": size,
                            "color": rgb_color
                        })
    
    # Sort blocks by page number then by vertical position (y-coordinate)
    text_blocks.sort(key=lambda block: (block["page_num"], block["position"][1]))
    return text_blocks

def create_deidentified_pdf(text_blocks, output_path):
    c = canvas.Canvas(output_path, pagesize=letter)
    page_height = letter[1]
    current_page = -1

    # font_mapping = {
    #     "Aptos-Bold": "Helvetica-Bold",
    #     "Aptos-Regular": "Helvetica",
    # }

    for block in text_blocks:
        page_num = block["page_num"]
        if page_num != current_page:
            if current_page != -1:
                c.showPage()
            current_page = page_num

        text = block["text"]
        x0, y0, x1, y1 = block["position"]
        y0_adjusted = page_height - y0

        font_name = block.get("font", "Helvetica")
        if "," in font_name:
            font_name = font_name.replace(",", "-")
        # if font_name in font_mapping:
        #     font_name = font_mapping[font_name]
        font_size = block.get("size", 12)
        color = block.get("color", (0, 0, 0))
        
        try:
            c.setFont(font_name, font_size)
        except Exception as e:
            c.setFont("Helvetica", font_size)
        c.setFillColorRGB(*color)
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
            if " - " in text:
                field, value = text.split(" - ", 1) 
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