from surya.texify import TexifyPredictor
from surya.table_rec import TableRecPredictor
from surya.recognition import RecognitionPredictor
from surya.ocr_error import OCRErrorPredictor
from surya.layout import LayoutPredictor
from surya.detection import DetectionPredictor, InlineDetectionPredictor
import os
# Transformers uses .isin for an op, which is not supported on MPS
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"


def create_model_dict(device=None, dtype=None) -> dict:
    return {
        "layout_model": LayoutPredictor(device=device, dtype=dtype),
        "texify_model": TexifyPredictor(device=device, dtype=dtype),
        "recognition_model": RecognitionPredictor(device=device, dtype=dtype),
        "table_rec_model": TableRecPredictor(device=device, dtype=dtype),
        "detection_model": DetectionPredictor(device=device, dtype=dtype),
        "inline_detection_model": InlineDetectionPredictor(device=device, dtype=dtype),
        "ocr_error_model": OCRErrorPredictor(device=device, dtype=dtype)
    }
