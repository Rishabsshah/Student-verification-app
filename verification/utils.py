import hashlib

def generate_identity_hash(name: str, enrollment: str, college: str) -> str:
    """
    Generates a unique hash based on student name, enrollment number, and college.
    
    Logic:
    1. Concatenate: name + enrollment + college (normalized)
    2. Hash: SHA256
    3. Truncate: Remove last 5 characters (as per user request)
    
    Returns the truncated hex digest.
    """
    # Normalize inputs to ensure consistency
    # Remove spaces and convert to uppercase
    normalized_str = f"{name.strip().upper()}{enrollment.strip().upper()}{college.strip().upper()}"
    
    # Generate SHA256 hash
    full_hash = hashlib.sha256(normalized_str.encode('utf-8')).hexdigest()
    
    # Truncate: Remove last 5 digits
    truncated_hash = full_hash[:-5]
    
    return truncated_hash
