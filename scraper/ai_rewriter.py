"""
AI Article Rewriter using Groq (OpenAI-compatible API)
Rewrites article titles and content while preserving facts and meaning.
"""
import logging
import re
from openai import OpenAI
from decouple import config

logger = logging.getLogger(__name__)

# Use the Groq API via the OpenAI SDK
_client = None

def get_client():
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=config('OPENAI_API_KEY'),
            base_url=config('OPENAI_API_BASE', default='https://api.groq.com/openai/v1'),
        )
    return _client


AI_MODEL = config('AI_MODEL', default='llama-3.3-70b-versatile')


TITLE_PROMPT = """Rephrase this news headline into different natural-sounding words, keeping the exact same facts and meaning. Return ONLY the rephrased headline, no extra commentary:

Original: {title}"""


CONTENT_PROMPT = """You are a professional news editor. Rewrite the following article in your own original words. 

Rules:
- Keep ALL the facts, names, numbers, dates, and key information EXACTLY the same
- Use completely different sentence structures and vocabulary
- Write in a clear, engaging journalistic style
- Do NOT add any new information, opinions, or commentary
- Do NOT include any introduction like "Here is the rewritten article:" - just give the rewritten content
- Return plain HTML with <p> tags only (no <h1>, <h2>, images or other elements)
- Keep the same length approximately

Article to rewrite:
{content}"""


def rewrite_title(title: str) -> str:
    """Rephrase the article headline using AI."""
    try:
        client = get_client()
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "user", "content": TITLE_PROMPT.format(title=title)}
            ],
            max_tokens=150,
            temperature=0.7,
        )
        rewritten = response.choices[0].message.content.strip()
        # Strip quotes if the AI wrapped it in them
        rewritten = rewritten.strip('"\'')
        if rewritten:
            logger.info(f"Title rewritten: '{title}' -> '{rewritten}'")
            return rewritten
    except Exception as e:
        logger.warning(f"AI title rewrite failed: {e}")
    return title  # Fall back to original on failure


def rewrite_content(content: str) -> str:
    """Rewrite full article content using AI, preserving all facts."""
    if not content:
        return content
    
    # Strip HTML to get plain text for the prompt (AI works better on plain text)
    plain_text = re.sub(r'<[^>]+>', ' ', content)
    plain_text = re.sub(r'\s+', ' ', plain_text).strip()

    # Skip if content is too short (less than 100 chars) - not worth rewriting
    if len(plain_text) < 100:
        return content

    try:
        client = get_client()
        
        # Groq has token limits so truncate very long articles before sending
        # llama-3.3-70b supports large context but keep it under ~4000 words
        if len(plain_text) > 15000:
            plain_text = plain_text[:15000] + '...'

        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional news editor who rewrites articles in original language while keeping all facts intact."
                },
                {
                    "role": "user",
                    "content": CONTENT_PROMPT.format(content=plain_text)
                }
            ],
            max_tokens=2048,
            temperature=0.7,
        )
        rewritten = response.choices[0].message.content.strip()
        
        if rewritten and len(rewritten) > 100:
            # Ensure it has <p> tags for proper rendering on site
            if '<p>' not in rewritten:
                # Wrap paragraphs in <p> tags if AI returned plain text
                paragraphs = [p.strip() for p in rewritten.split('\n\n') if p.strip()]
                rewritten = '\n'.join(f'<p>{p}</p>' for p in paragraphs)
            logger.info(f"Content rewritten: {len(plain_text)} chars -> {len(rewritten)} chars")
            return rewritten

    except Exception as e:
        logger.warning(f"AI content rewrite failed: {e}")

    return content  # Fall back to original on failure
