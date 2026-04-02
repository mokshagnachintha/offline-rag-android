"""
advanced_metrics.py — Research-grade evaluation metrics for O-RAG

Implements three metric categories:
1. TEXT METRICS (RAGAS-style):
   - Context Recall: Does retrieved context contain the answer facts?
   - Faithfulness: Does response stick to provided context?
   - Answer Relevance: Is response relevant to the question?
   - Answer Correctness: F1 score vs ground truth

2. VISION METRICS:
   - Image Clarity: Is extracted image legible? (Laplacian variance)
   - Layout Preservation: Text position in images maintained?
   - Bounding Box Accuracy: Are images correctly associated with chunks?

3. MULTIMODAL METRICS:
   - Text-Image Relevance: Does image match question intent?
   - Cross-modal Consistency: Do text answer + image answer align?
   - Multimodal F1: Combined score from text and visual understanding
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from collections import Counter
import math
import json


@dataclass
class TextMetrics:
    """Container for text-based evaluation metrics"""
    context_recall: float = 0.0  # 0-1: Does context contain answer facts?
    faithfulness: float = 0.0    # 0-1: Does response stick to context?
    answer_relevance: float = 0.0  # 0-1: Is response relevant to question?
    answer_f1: float = 0.0       # 0-1: F1 vs ground truth answer
    
    def to_dict(self) -> Dict:
        return {
            'context_recall': round(self.context_recall, 3),
            'faithfulness': round(self.faithfulness, 3),
            'answer_relevance': round(self.answer_relevance, 3),
            'answer_f1': round(self.answer_f1, 3),
        }


@dataclass
class VisionMetrics:
    """Container for vision-based evaluation metrics"""
    image_clarity: float = 0.0   # 0-1: Image legibility (Laplacian variance)
    layout_preservation: float = 0.0  # 0-1: Text position maintained
    bbox_accuracy: float = 0.0   # 0-1: Correct image-chunk association
    
    def to_dict(self) -> Dict:
        return {
            'image_clarity': round(self.image_clarity, 3),
            'layout_preservation': round(self.layout_preservation, 3),
            'bbox_accuracy': round(self.bbox_accuracy, 3),
        }


@dataclass
class MultimodalMetrics:
    """Container for multimodal evaluation metrics"""
    text_image_relevance: float = 0.0  # 0-1: Image matches question intent
    cross_modal_consistency: float = 0.0  # 0-1: Text and image answers align
    multimodal_f1: float = 0.0  # 0-1: Combined text+visual F1
    
    def to_dict(self) -> Dict:
        return {
            'text_image_relevance': round(self.text_image_relevance, 3),
            'cross_modal_consistency': round(self.cross_modal_consistency, 3),
            'multimodal_f1': round(self.multimodal_f1, 3),
        }


# ========================================================================
# TEXT METRICS
# ========================================================================

class TextMetricsCalculator:
    """Calculate RAGAS-style text evaluation metrics"""
    
    @staticmethod
    def context_recall(context_text: str, ground_truth: str, response: str) -> float:
        """
        Measure: Does the retrieved context contain the answer facts?
        
        Method:
        1. Extract key entities from ground truth
        2. Check if they appear in context
        3. Return recall@context
        
        Range: [0, 1]
        - 0.0: Context doesn't mention key facts from ground truth
        - 1.0: Context contains all key facts
        """
        truth_facts = _extract_entities(ground_truth)
        context_facts = _extract_entities(context_text)
        
        if not truth_facts:
            return 1.0  # No facts to recall = perfect score
        
        matches = sum(1 for fact in truth_facts if fact in context_facts)
        return matches / len(truth_facts)
    
    @staticmethod
    def faithfulness(context_text: str, response: str) -> float:
        """
        Measure: Does the response stick to provided context?
        (Avoids hallucinations from out-of-context facts)
        
        Method:
        1. Extract key entities from response
        2. Check if they appear in context
        3. Return faithfulness score (% of response facts in context)
        
        Range: [0, 1]
        - 0.0: Response is entirely hallucinated (no context facts)
        - 1.0: Every fact in response comes from context
        """
        response_facts = _extract_entities(response)
        context_facts = _extract_entities(context_text)
        
        if not response_facts:
            return 1.0  # Empty response = not hallucinating
        
        matches = sum(1 for fact in response_facts if fact in context_facts)
        return matches / len(response_facts)
    
    @staticmethod
    def answer_relevance(question: str, response: str) -> float:
        """
        Measure: Is the response relevant to the question?
        
        Method:
        1. Extract keywords from question and response
        2. Compute token overlap ratio
        3. Penalize responses that ignore the question
        
        Range: [0, 1]
        - 0.0: Response has no overlap with question
        - 1.0: Response directly addresses question
        """
        q_tokens = set(_tokenize(question.lower()))
        r_tokens = set(_tokenize(response.lower()))
        
        if not q_tokens:
            return 1.0
        
        overlap = q_tokens & r_tokens
        return len(overlap) / len(q_tokens)
    
    @staticmethod
    def answer_f1(response: str, ground_truth: str) -> float:
        """
        Measure: How similar is response to ground truth? (F1 score)
        
        Method:
        1. Tokenize response and ground truth
        2. Compute precision: % of response tokens in ground truth
        3. Compute recall: % of ground truth tokens in response
        4. Return F1 = 2 * (precision * recall) / (precision + recall)
        
        Range: [0, 1]
        - 0.0: Response and ground truth have no overlap
        - 1.0: Response matches ground truth exactly
        """
        response_tokens = _tokenize(response.lower())
        truth_tokens = _tokenize(ground_truth.lower())
        
        common = Counter(response_tokens) & Counter(truth_tokens)
        num_same = sum(common.values())
        
        if len(response_tokens) == 0 or len(truth_tokens) == 0:
            return 1.0 if response == ground_truth else 0.0
        
        precision = num_same / len(response_tokens)
        recall = num_same / len(truth_tokens)
        
        if precision + recall == 0:
            return 0.0
        
        return 2 * (precision * recall) / (precision + recall)


# ========================================================================
# VISION METRICS
# ========================================================================

class VisionMetricsCalculator:
    """Calculate vision-based evaluation metrics"""
    
    @staticmethod
    def image_clarity(image_array: Optional[np.ndarray]) -> float:
        """
        Measure: Is extracted image legible? (Laplacian variance)
        
        Method:
        1. Compute Laplacian edge detection
        2. Calculate variance of edges
        3. Higher variance = sharper, more legible image
        
        Range: [0, 1] (normalized)
        - 0.0: Image is blurry or unreadable
        - 1.0: Image is clear and sharp
        """
        if image_array is None:
            return 0.0
        
        try:
            # Fallback: simple gradient-based clarity score
            # (assumes image is grayscale or we can compute on all channels)
            if len(image_array.shape) == 3:
                # Convert RGB to grayscale
                image_gray = np.mean(image_array, axis=2)
            else:
                image_gray = image_array
            
            # Compute horizontal and vertical gradients
            grad_x = np.diff(image_gray, axis=0)
            grad_y = np.diff(image_gray, axis=1)
            
            # Clarity = variance of gradients (normalized)
            clarity_score = (np.var(grad_x) + np.var(grad_y)) / 2
            
            # Normalize to [0, 1] range (empirical: typical clarity values 0-50000)
            normalized = min(1.0, clarity_score / 10000)
            return float(normalized)
        except Exception:
            return 0.5  # Unknown image format
    
    @staticmethod
    def layout_preservation(original_bbox: Tuple[float, float, float, float],
                            extracted_bbox: Tuple[float, float, float, float]) -> float:
        """
        Measure: Was text position in image maintained during extraction?
        
        Method:
        1. Original: (x0, y0, x1, y1) in PDF coordinates
        2. Extracted: (x0', y0', x1', y1') in extracted image
        3. Score: 1 - (normalized bbox distance)
        
        Range: [0, 1]
        - 0.0: Bounding box severely distorted
        - 1.0: Bounding box perfectly preserved
        """
        x0, y0, x1, y1 = original_bbox
        x0p, y0p, x1p, y1p = extracted_bbox
        
        # Compute distance
        dist = math.sqrt((x0 - x0p)**2 + (y0 - y0p)**2 + 
                        (x1 - x1p)**2 + (y1 - y1p)**2)
        
        # Normalize by image diagonal (empirical: typical diagonal ~1000px)
        normalized_dist = dist / 1000.0
        
        return max(0.0, 1.0 - normalized_dist)
    
    @staticmethod
    def bbox_accuracy(extracted_text: str, associated_chunk_text: str) -> float:
        """
        Measure: Is extracted image correctly associated with its chunk?
        
        Method:
        1. Extract entities from image text (OCR or metadata)
        2. Extract entities from chunk text
        3. Compute Jaccard similarity (intersection / union)
        
        Range: [0, 1]
        - 0.0: Image and chunk have no semantic connection
        - 1.0: Image and chunk perfectly aligned
        """
        img_entities = _extract_entities(extracted_text)
        chunk_entities = _extract_entities(associated_chunk_text)
        
        if not img_entities and not chunk_entities:
            return 1.0  # Both empty = consistent
        
        if not img_entities or not chunk_entities:
            return 0.0  # One empty, other not = inconsistent
        
        intersection = len(img_entities & chunk_entities)
        union = len(img_entities | chunk_entities)
        
        return intersection / union if union > 0 else 0.0


# ========================================================================
# MULTIMODAL METRICS
# ========================================================================

class MultimodalMetricsCalculator:
    """Calculate multimodal evaluation metrics"""
    
    @staticmethod
    def text_image_relevance(question: str, retrieved_image_metadata: Dict) -> float:
        """
        Measure: Does retrieved image match the question intent?
        
        Method:
        1. Extract question keywords
        2. Check image metadata (title, caption, alt-text, associated chunk)
        3. Compute keyword overlap
        
        Range: [0, 1]
        - 0.0: Image is irrelevant to question
        - 1.0: Image directly answers question
        """
        q_keywords = set(_tokenize(question.lower()))
        
        # Aggregate image metadata
        img_text_parts = [
            retrieved_image_metadata.get('caption', ''),
            retrieved_image_metadata.get('alt_text', ''),
            retrieved_image_metadata.get('associated_chunk', ''),
        ]
        img_keywords = set(_tokenize(' '.join(img_text_parts).lower()))
        
        if not q_keywords or not img_keywords:
            return 0.5  # Unknown relevance
        
        overlap = q_keywords & img_keywords
        return len(overlap) / len(q_keywords)
    
    @staticmethod
    def cross_modal_consistency(text_answer: str, image_description: str) -> float:
        """
        Measure: Do text and image meanings align?
        
        Method:
        1. Extract facts from text answer
        2. Extract facts from image description (OCR or manual)
        3. Check for contradictions
        4. Compute consistency score
        
        Range: [0, 1]
        - 0.0: Text and image answers contradict
        - 1.0: Text and image answers are consistent
        """
        text_facts = _extract_entities(text_answer)
        img_facts = _extract_entities(image_description)
        
        if not text_facts or not img_facts:
            return 0.5  # Can't assess without facts
        
        # Jaccard similarity for consistency
        intersection = len(text_facts & img_facts)
        union = len(text_facts | img_facts)
        
        consistency = intersection / union if union > 0 else 0.0
        return consistency
    
    @staticmethod
    def multimodal_f1(text_f1: float, image_f1: float, weight_text: float = 0.65) -> float:
        """
        Measure: Combined score from text and visual understanding
        
        Method:
        1. Weighted average: (weight_text * text_f1) + (1 - weight_text) * image_f1
        2. Default: 65% weight to text (more reliable), 35% to image
        
        Range: [0, 1]
        - 0.0: Both text and image components failed
        - 1.0: Both text and image components succeeded
        """
        return weight_text * text_f1 + (1 - weight_text) * image_f1


# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

def _tokenize(text: str) -> List[str]:
    """Simple whitespace + punctuation tokenizer"""
    import string
    text = text.translate(str.maketrans('', '', string.punctuation))
    return text.split()


def _extract_entities(text: str) -> set:
    """
    Extract Named Entities (NER-style) using simple rules.
    
    For research/mobile context:
    - Numbers (measurements, values)
    - Capitalized phrases (names, terms)
    - Domain keywords (medical: "patient", "symptom"; tech: "database", "API")
    """
    entities = set()
    
    # Rule 1: Multi-word capitalized phrases (Names, Terms)
    import re
    capitalized_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
    entities.update(capitalized_phrases)
    
    # Rule 2: Numbers with units (measurements)
    measurements = re.findall(r'\d+(?:\.\d+)?(?:\s*(?:mg|ml|kg|cm|mm|%|°C|mmHg))?', text)
    entities.update(measurements)
    
    # Rule 3: Domain keywords (basic set)
    domain_keywords = [
        'disease', 'symptom', 'treatment', 'diagnosis', 'medication',
        'patient', 'hospital', 'clinical', 'data', 'analysis',
        'database', 'api', 'server', 'network', 'tcp', 'http',
        'contract', 'agreement', 'liability', 'compliance', 'regulation',
        'invoice', 'expense', 'revenue', 'profit', 'budget'
    ]
    for keyword in domain_keywords:
        if keyword.lower() in text.lower():
            entities.add(keyword)
    
    return entities


def calculate_all_metrics(
    question: str,
    retrieved_context: str,
    generated_response: str,
    ground_truth_answer: str,
    image_data: Optional[Dict] = None,
) -> Dict:
    """
    Comprehensive metric calculation wrapper
    
    Args:
        question: User question
        retrieved_context: Top-k retrieved chunks
        generated_response: LLM-generated answer
        ground_truth_answer: Gold-standard answer
        image_data: Optional image metadata (for multimodal eval)
    
    Returns:
        Dict with all metric categories
    """
    result = {
        'text_metrics': TextMetricsCalculator.context_recall(
            retrieved_context, ground_truth_answer, generated_response
        ),
    }
    
    # Text metrics
    text_metrics = TextMetrics(
        context_recall=TextMetricsCalculator.context_recall(
            retrieved_context, ground_truth_answer, generated_response
        ),
        faithfulness=TextMetricsCalculator.faithfulness(
            retrieved_context, generated_response
        ),
        answer_relevance=TextMetricsCalculator.answer_relevance(
            question, generated_response
        ),
        answer_f1=TextMetricsCalculator.answer_f1(
            generated_response, ground_truth_answer
        ),
    )
    
    result['text'] = text_metrics.to_dict()
    
    # Vision metrics (if image data provided)
    if image_data:
        vision_metrics = VisionMetricsCalculator(
            image_clarity=VisionMetricsCalculator.image_clarity(
                image_data.get('image_array')
            ),
            layout_preservation=VisionMetricsCalculator.layout_preservation(
                image_data.get('original_bbox', (0, 0, 1, 1)),
                image_data.get('extracted_bbox', (0, 0, 1, 1))
            ),
            bbox_accuracy=VisionMetricsCalculator.bbox_accuracy(
                image_data.get('extracted_text', ''),
                retrieved_context
            ),
        )
        result['vision'] = vision_metrics.to_dict()
    
    # Multimodal metrics (if image data provided)
    if image_data:
        multimodal_metrics = MultimodalMetricsCalculator(
            text_image_relevance=MultimodalMetricsCalculator.text_image_relevance(
                question, image_data
            ),
            cross_modal_consistency=MultimodalMetricsCalculator.cross_modal_consistency(
                generated_response, image_data.get('image_description', '')
            ),
            multimodal_f1=MultimodalMetricsCalculator.multimodal_f1(
                text_metrics.answer_f1,
                VisionMetricsCalculator.bbox_accuracy(
                    image_data.get('extracted_text', ''),
                    retrieved_context
                )
            ),
        )
        result['multimodal'] = multimodal_metrics.to_dict()
    
    return result


if __name__ == '__main__':
    # Quick test
    test_question = "What are the symptoms of diabetes?"
    test_context = "Diabetes is characterized by high blood sugar levels. Common symptoms include increased thirst, frequent urination, and fatigue."
    test_response = "The main symptoms of diabetes are increased thirst, frequent urination, and feeling tired all the time."
    test_ground_truth = "Symptoms of diabetes include increased thirst (polydipsia), frequent urination (polyuria), fatigue, and weight loss."
    
    metrics = calculate_all_metrics(
        test_question, test_context, test_response, test_ground_truth
    )
    
    print("=" * 60)
    print("METRICS TEST")
    print("=" * 60)
    print(json.dumps(metrics, indent=2))
