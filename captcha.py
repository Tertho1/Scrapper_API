import cv2
import pytesseract
import numpy as np

# 1. Load & grayscale
image = cv2.imread("captcha_image.jpg")
gray  = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 2. Median blur to remove salt‑and‑pepper noise
median = cv2.medianBlur(gray, 3)

# 3. Gaussian blur for additional smoothing
gauss = cv2.GaussianBlur(median, (3, 3), 0)

# 4. Morphological closing to fill small holes/gaps
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
morph  = cv2.morphologyEx(gauss, cv2.MORPH_CLOSE, kernel, iterations=1)

# 5. Adaptive thresholding for binarization
thresh = cv2.adaptiveThreshold(
    morph, 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY_INV,
    blockSize=11,
    C=2
)

# 6. Detect & remove line noise with Hough + inpainting
edges = cv2.Canny(thresh, 50, 150)
lines = cv2.HoughLinesP(
    edges, 1, np.pi/180,
    threshold=100,
    minLineLength=50,
    maxLineGap=5
)
mask = np.zeros_like(gray)
if lines is not None:
    for x1, y1, x2, y2 in lines.squeeze():
        cv2.line(mask, (x1, y1), (x2, y2), 255, 2)
clean = cv2.inpaint(thresh, mask, 3, cv2.INPAINT_TELEA)

# 7. OCR with Tesseract
config = (
    "--oem 3 "
    "--psm 8 "
    "-c tessedit_char_whitelist=0123456789 "
    "--dpi 70"
)
result = pytesseract.image_to_string(clean, config=config)

print("Detected Text:", result.strip())
