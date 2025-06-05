from typing import Optional, List
import json
from app.llm_clients import generate_text_completion
from app.config import TEST_MODE
from app.utils import load_prompt # Import the new utility

MAX_TWEET_LENGTH = 280

async def generate_tweet_thread(
    topic: str,
    num_tweets: int = 3,
    style_tone: Optional[str] = None,
    call_to_action: Optional[str] = None,
    custom_instructions: Optional[str] = None # Added for consistency
) -> List[str]:
    """
    Generates a tweet thread on a given topic using the configured LLM.
    Attempts to return a list of strings, each representing a tweet.
    """
    if TEST_MODE:
        return [f"Test Mode: Tweet {i+1}/{num_tweets} about '{topic}'. Style: {style_tone}. CTA: {call_to_action}. Instructions: {custom_instructions}" for i in range(num_tweets)]

    call_to_action_section_str = ""
    if call_to_action:
        call_to_action_section_str = f"The last tweet should include this call to action: '{call_to_action}'."

    custom_instructions_section_str = ""
    if custom_instructions:
        custom_instructions_section_str = f"Follow these additional instructions: {custom_instructions}"

    prompt = load_prompt(
        "tweet_thread_generator_prompt.txt",
        num_tweets=str(num_tweets), # Ensure it's a string for .format
        topic=topic,
        style_tone=style_tone if style_tone else "neutral",
        call_to_action_section=call_to_action_section_str,
        custom_instructions_section=custom_instructions_section_str
    )

    if prompt.startswith("Error:"): # Check for errors from load_prompt
        return [prompt] # Propagate error in a list, as function returns List[str]

    # Calculate max_tokens: num_tweets * average tokens per tweet (e.g. 280 chars / 4 chars_per_token * 1.5 safety factor)
    # Plus some overhead for JSON formatting.
    # Max chars per tweet: 280. Avg chars per token ~4. So ~70 tokens per tweet.
    # For safety and JSON structure, let's say 150 tokens per tweet.
    calculated_max_tokens = (num_tweets * 150) + 200 # 200 for JSON overhead and general buffer

    raw_llm_output = await generate_text_completion(
        prompt=prompt,
        temperature=0.6, # Slightly lower temp for more structured output
        max_tokens=calculated_max_tokens
    )

    if raw_llm_output.startswith("Error:"):
        return [raw_llm_output] # Propagate error

    try:
        # Attempt to find JSON block if LLM includes preamble/postamble
        json_start_index = raw_llm_output.find('[')
        json_end_index = raw_llm_output.rfind(']')

        if json_start_index != -1 and json_end_index != -1 and json_end_index > json_start_index:
            json_str = raw_llm_output[json_start_index : json_end_index+1]
            tweet_list = json.loads(json_str)
            if isinstance(tweet_list, list) and all(isinstance(tweet, str) for tweet in tweet_list):
                # Optional: Trim tweets if they exceed MAX_TWEET_LENGTH, or let frontend handle it
                # For now, return as is.
                return tweet_list
            else:
                return ["Error: LLM did not return a valid JSON list of tweet strings. Parsed: " + str(tweet_list)[:300]]
        else:
            # Fallback: if no JSON array, try to split by common delimiters or return as single block
            # This part can be improved with more sophisticated parsing.
            # For now, if not valid JSON, return an error indicating this.
            return ["Error: LLM output was not in the expected JSON array format. Output:\n" + raw_llm_output[:500]] # Show first 500 chars

    except json.JSONDecodeError:
        return ["Error: Failed to decode JSON from LLM output for tweet thread. Output:\n" + raw_llm_output[:500]]
    except Exception as e:
        return [f"Error processing LLM output for tweet thread: {str(e)}. Output:\n" + raw_llm_output[:500]]

# Example usage (optional)
# if __name__ == "__main__":
#     import asyncio
#     async def test_tweets():
#         topic = "The Importance of Daily Exercise"
#         # from app.config import LLM_PROVIDER, ANTHROPIC_KEY
#         # print(f"Using LLM Provider: {LLM_PROVIDER}")
#         # if LLM_PROVIDER == 'anthropic' and not ANTHROPIC_KEY:
#         #     print("ANTHROPIC_KEY not set. Exiting.")
#         #     return

#         tweets = await generate_tweet_thread(topic, num_tweets=3, style_tone="motivational", call_to_action="Get moving today!", custom_instructions="Include an emoji in each tweet.")
#         print(f"--- Tweet Thread on: {topic} ---")
#         if tweets and tweets[0].startswith("Error:"):
#             print(tweets[0])
#         else:
#             for i, tweet in enumerate(tweets):
#                 print(f"Tweet {i+1}: {tweet} (Length: {len(tweet)})")

#         # Test TEST_MODE
#         # from app import config
#         # config.TEST_MODE = True
#         # test_mode_tweets = await generate_tweet_thread("Test Topic", 2, "test style", "test cta", "test instructions")
#         # print(f"\n--- Test Mode Tweets ---")
#         # for i, tweet in enumerate(test_mode_tweets):
#         #     print(f"Tweet {i+1}: {tweet}")

#     asyncio.run(test_tweets())
