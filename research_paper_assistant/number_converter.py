from typing import List

class NumberConverter:
    ROMAN_NUMS = {
        'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5,
        'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10,
        'xi': 11, 'xii': 12, 'xiii': 13, 'xiv': 14, 'xv': 15,
        'xvi': 16, 'xvii': 17, 'xviii': 18, 'xix': 19, 'xx': 20
    }
    
    ARABIC_TO_ROMAN = {v: k for k, v in ROMAN_NUMS.items()}
    
    @staticmethod
    def contains_number(text: str) -> bool:
        """Check if text contains any number (roman or arabic)"""
        text = text.lower()
        # Check for arabic numbers
        if any(c.isdigit() for c in text):
            return True
        # Check for roman numbers
        return any(roman in text for roman in NumberConverter.ROMAN_NUMS.keys())
    
    @staticmethod
    def get_all_number_variants(query: str) -> List[str]:
        """Get all possible number variants of a query string"""
        variants = {query.lower()}
        query_lower = query.lower()
        words = query_lower.split()
        
        for i, word in enumerate(words):
            # Convert roman to arabic
            if word in NumberConverter.ROMAN_NUMS:
                arabic = str(NumberConverter.ROMAN_NUMS[word])
                new_words = words.copy()
                new_words[i] = arabic
                variants.add(' '.join(new_words))
            
            # Convert arabic to roman
            if word.isdigit() and int(word) in NumberConverter.ARABIC_TO_ROMAN:
                roman = NumberConverter.ARABIC_TO_ROMAN[int(word)]
                new_words = words.copy()
                new_words[i] = roman
                variants.add(' '.join(new_words))
        
        return list(variants)
    
    @staticmethod
    def is_number_match(text: str, query: str) -> bool:
        """Check if query matches text, considering number variants"""
        text = text.lower()
        variants = NumberConverter.get_all_number_variants(query)
        return any(variant in text for variant in variants)