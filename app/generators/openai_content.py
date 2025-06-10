from openai import AsyncOpenAI
from ..config import OPENAI_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS

client = AsyncOpenAI(api_key=OPENAI_KEY)

async def generate_content_with_openai(prompt: str, system_prompt: str = None) -> str:
    """
    Generate content using OpenAI's API.
    
    Args:
        prompt (str): The main prompt for content generation
        system_prompt (str, optional): System prompt to guide the model's behavior
    
    Returns:
        str: Generated content
    """
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

async def generate_story_openai(character_description: str) -> str:
    """Generate a story using OpenAI."""
    system_prompt = """You are a creative storyteller. Create engaging, well-structured stories 
    that are suitable for video adaptation. Focus on vivid descriptions and clear scene transitions."""
    
    prompt = f"""Create a short story based on this character description: {character_description}
    The story should be engaging and suitable for video adaptation with clear scenes."""
    
    return await generate_content_with_openai(prompt, system_prompt)

async def generate_educational_content_openai(
    topic: str,
    style: str = "lecture",
    difficulty: str = "intermediate"
) -> str:
    """Generate educational content using OpenAI."""
    system_prompt = """You are an expert educator. Create clear, engaging educational content 
    that is well-structured and easy to understand."""
    
    prompt = f"""Create educational content about {topic} in a {style} style.
    The content should be at a {difficulty} difficulty level.
    Include clear explanations and examples where appropriate."""
    
    return await generate_content_with_openai(prompt, system_prompt)

async def generate_podcast_script_openai(
    topic: str,
    style: str = "professional",
    length_words: int = 500
) -> str:
    """Generate a podcast script using OpenAI."""
    system_prompt = """You are a professional podcast host. Create engaging, conversational 
    podcast scripts that are informative and entertaining."""
    
    prompt = f"""Create a podcast script about {topic} in a {style} style.
    The script should be approximately {length_words} words long.
    Include an introduction, main content, and conclusion."""
    
    return await generate_content_with_openai(prompt, system_prompt)

async def generate_article_openai(
    topic: str,
    style: str = "professional",
    length_words: int = 800,
    custom_instructions: str = None
) -> str:
    """Generate an article using OpenAI."""
    system_prompt = """You are a professional writer. Create well-structured, engaging articles 
    that are informative and maintain reader interest."""
    
    prompt = f"""Create an article about {topic} in a {style} style.
    The article should be approximately {length_words} words long.
    {custom_instructions if custom_instructions else ''}"""
    
    return await generate_content_with_openai(prompt, system_prompt)

async def generate_tweet_thread_openai(
    topic: str,
    num_tweets: int = 3,
    style: str = "professional",
    call_to_action: str = None
) -> list:
    """Generate a tweet thread using OpenAI."""
    system_prompt = """You are a social media expert. Create engaging tweet threads that 
    are informative and maintain reader interest throughout."""
    
    prompt = f"""Create a thread of {num_tweets} tweets about {topic} in a {style} style.
    {f'End with a call to action: {call_to_action}' if call_to_action else ''}"""
    
    content = await generate_content_with_openai(prompt, system_prompt)
    # Split the content into individual tweets
    tweets = [tweet.strip() for tweet in content.split('\n') if tweet.strip()]
    return tweets[:num_tweets]

async def generate_book_chapter_openai(
    plot_summary: str = None,
    chapter_topic: str = None,
    previous_chapter: str = None,
    characters: list = None,
    genre: str = None,
    style: str = "narrative",
    length_words: int = 2000
) -> str:
    """Generate a book chapter using OpenAI."""
    system_prompt = """You are a professional novelist. Create engaging, well-structured book 
    chapters that maintain narrative flow and character development."""
    
    prompt = f"""Create a book chapter with the following details:
    {f'Plot Summary: {plot_summary}' if plot_summary else ''}
    {f'Chapter Topic: {chapter_topic}' if chapter_topic else ''}
    {f'Previous Chapter: {previous_chapter}' if previous_chapter else ''}
    {f'Characters: {", ".join(characters)}' if characters else ''}
    {f'Genre: {genre}' if genre else ''}
    Style: {style}
    Length: approximately {length_words} words"""
    
    return await generate_content_with_openai(prompt, system_prompt) 