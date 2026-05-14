import easyocr
import cv2


class OCREngine:
    def __init__(self):
        print("[INFO] Loading EasyOCR model...")

        self.reader = easyocr.Reader(
            ['en'],
            gpu=False
        )

        print("[INFO] OCR model loaded.")

    def extract_text(self, frame):
        """
        Extract text from frame
        """

        results = self.reader.readtext(frame)

        extracted_texts = []

        for result in results:
            bbox, text, confidence = result

            if confidence < 0.5:
                continue

            extracted_texts.append({
                "text": text,
                "confidence": confidence
            })

        return extracted_texts