import re

def extract_chapters(text):
    """
    Extract chapter descriptions from text containing chapter tags.
    Returns a list of tuples containing (chapter_number, description).
    
    Args:
        text (str): Text containing chapter tags in format <chapterX>description</chapterX>
        
    Returns:
        list: List of tuples (chapter_number, description)
    """
    # Pattern to match chapter tags and their content
    pattern = r'<chapter(\d+)>(.*?)</chapter\1>'
    
    # Find all matches in text, handling multiline content
    chapters = re.findall(pattern, text, re.DOTALL)
    
    # Convert to list of tuples, strip whitespace from descriptions
    chapters = [(int(num), desc.strip()) for num, desc in chapters]
    
    # Sort by chapter number
    chapters.sort(key=lambda x: x[0])
    
    return chapters

def format_chapters(chapters):
    """
    Format extracted chapters into a readable string.
    
    Args:
        chapters (list): List of (chapter_number, description) tuples
        
    Returns:
        str: Formatted chapter listing
    """
    formatted = []
    for num, desc in chapters:
        formatted.append(f"Chapter {num}:")
        formatted.append(desc)
        formatted.append("")  # Empty line between chapters
    
    return "\n".join(formatted)

# Example usage:
sample_text = """
<chapter0>Description of chapter 0</chapter0>
<chapter1>Description of chapter 1</chapter1>
"""

if __name__ == "__main__":
    # Get chapters
    chapters = extract_chapters(sample_text)
    
    # Print formatted output
    print(format_chapters(chapters))