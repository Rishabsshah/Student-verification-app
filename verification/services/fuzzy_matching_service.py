"""
Fuzzy String Matching Service for Triple-Lock Verification

This service handles name matching across different verification phases:
- OCR Name vs Aadhaar Name
- Aadhaar Name vs UPI Payer Name

Uses thefuzz library for intelligent fuzzy string matching.
"""

from thefuzz import fuzz
import re


class FuzzyMatchingService:
    """
    Handles fuzzy string matching for name verification across different sources.
    """
    
    # Default threshold for name matching (0-100)
    DEFAULT_THRESHOLD = 85
    
    @staticmethod
    def normalize_name(name):
        """
        Normalize a name for comparison by:
        - Converting to lowercase
        - Removing extra whitespace
        - Removing periods and commas
        - Removing common titles (Mr, Mrs, Dr, etc.)
        
        Args:
            name (str): Raw name string
            
        Returns:
            str: Normalized name
        """
        if not name:
            return ""
        
        # Convert to lowercase
        name = name.lower().strip()
        
        # Remove common titles
        titles = ['mr', 'mrs', 'ms', 'dr', 'prof', 'shri', 'smt', 'kumari']
        for title in titles:
            name = re.sub(rf'\b{title}\.?\s*', '', name)
        
        # Remove periods, commas, and extra punctuation
        name = re.sub(r'[.,;:]', '', name)
        
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    @staticmethod
    def match_names(name1, name2, threshold=None):
        """
        Compare two names using fuzzy matching and return match result.
        
        Uses multiple fuzzy matching algorithms:
        - Simple ratio: Direct character comparison
        - Partial ratio: Substring matching
        - Token sort ratio: Word-order independent matching
        
        Args:
            name1 (str): First name
            name2 (str): Second name
            threshold (float, optional): Minimum score to consider a match (0-100)
                                        Defaults to 85
        
        Returns:
            tuple: (is_match: bool, score: float, details: dict)
        
        Example:
            >>> FuzzyMatchingService.match_names("John Smith", "SMITH JOHN")
            (True, 90.5, {...})
        """
        if threshold is None:
            threshold = FuzzyMatchingService.DEFAULT_THRESHOLD
        
        # Handle empty names
        if not name1 or not name2:
            return False, 0.0, {
                'error': 'One or both names are empty',
                'name1': name1,
                'name2': name2
            }
        
        # Normalize names
        name1_clean = FuzzyMatchingService.normalize_name(name1)
        name2_clean = FuzzyMatchingService.normalize_name(name2)
        
        # Calculate different similarity scores
        ratio = fuzz.ratio(name1_clean, name2_clean)
        partial_ratio = fuzz.partial_ratio(name1_clean, name2_clean)
        token_sort_ratio = fuzz.token_sort_ratio(name1_clean, name2_clean)
        token_set_ratio = fuzz.token_set_ratio(name1_clean, name2_clean)
        
        # Weighted average (prioritize token_sort_ratio for name matching)
        # Token sort is best for names because it handles word order differences
        score = (
            ratio * 0.2 +           # 20% - basic similarity
            partial_ratio * 0.2 +   # 20% - substring matching
            token_sort_ratio * 0.4 + # 40% - word-order independent (most important)
            token_set_ratio * 0.2   # 20% - token set matching
        )
        
        # Round to 2 decimal places
        score = round(score, 2)
        
        # Determine if it's a match
        is_match = score >= threshold
        
        # Prepare details
        details = {
            'name1_original': name1,
            'name2_original': name2,
            'name1_normalized': name1_clean,
            'name2_normalized': name2_clean,
            'scores': {
                'ratio': ratio,
                'partial_ratio': partial_ratio,
                'token_sort_ratio': token_sort_ratio,
                'token_set_ratio': token_set_ratio,
                'weighted_average': score
            },
            'threshold': threshold,
            'is_match': is_match
        }
        
        return is_match, score, details
    
    @staticmethod
    def batch_match(reference_name, candidate_names, threshold=None):
        """
        Match a reference name against multiple candidate names.
        Returns the best match.
        
        Args:
            reference_name (str): The reference name to match against
            candidate_names (list): List of candidate names
            threshold (float, optional): Minimum score to consider a match
        
        Returns:
            dict: Best match result with score, name, and details
        
        Example:
            >>> FuzzyMatchingService.batch_match(
            ...     "John Smith",
            ...     ["SMITH J", "Jane Doe", "JOHN SMITH"]
            ... )
            {'best_match': 'JOHN SMITH', 'score': 95.0, ...}
        """
        if threshold is None:
            threshold = FuzzyMatchingService.DEFAULT_THRESHOLD
        
        if not candidate_names:
            return {
                'best_match': None,
                'score': 0.0,
                'is_match': False,
                'all_scores': []
            }
        
        results = []
        for candidate in candidate_names:
            is_match, score, details = FuzzyMatchingService.match_names(
                reference_name, 
                candidate, 
                threshold
            )
            results.append({
                'candidate': candidate,
                'score': score,
                'is_match': is_match,
                'details': details
            })
        
        # Sort by score (descending)
        results.sort(key=lambda x: x['score'], reverse=True)
        best = results[0]
        
        return {
            'best_match': best['candidate'],
            'score': best['score'],
            'is_match': best['is_match'],
            'details': best['details'],
            'all_scores': results
        }
    
    @staticmethod
    def get_similarity_level(score):
        """
        Get a human-readable similarity level based on score.
        
        Args:
            score (float): Similarity score (0-100)
        
        Returns:
            str: Similarity level description
        """
        if score >= 95:
            return "Excellent Match"
        elif score >= 85:
            return "Good Match"
        elif score >= 75:
            return "Fair Match"
        elif score >= 60:
            return "Partial Match"
        elif score >= 40:
            return "Weak Match"
        else:
            return "No Match"
