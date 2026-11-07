
"""
Deterministic compression engine for token reduction.

Implements "caveman-style" compression: shortening text to essential meaning
while preserving recoverability via MCP (Model Context Protocol) references.
"""

import re
import hashlib
from dataclasses import dataclass
from typing import Optional


@dataclass
class CompressionResult:
    """Result of a compression operation."""
    original_text: str
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    savings: int
    mcp_reference: Optional[str] = None


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    Uses a more accurate approximation based on character count and word boundaries.
    """
    if not text:
        return 0
    # More accurate estimation: ~3.5-4 chars per token for English text
    # Count characters excluding whitespace as a baseline
    char_count = len(text)
    # Add bonus for word boundaries (spaces, punctuation)
    word_boundaries = len(re.findall(r'[\s\.,!?;:()\[\]{}]', text))
    # Rough formula: (chars + boundaries) / 3.5
    return max(1, (char_count + word_boundaries) // 3)


def compress_text(text: str, mode: str = "compress") -> CompressionResult:
    """
    Apply deterministic compression to text.

    Args:
        text: Input text to compress
        mode: "compress" for abbreviation, "summarize" for summary, "off" for no compression

    Returns:
        CompressionResult with compressed text and metadata
    """
    if not text or mode == "off":
        original_tokens = estimate_tokens(text)
        return CompressionResult(
            original_text=text,
            compressed_text=text,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            savings=0,
            mcp_reference=None,
        )

    original_tokens = estimate_tokens(text)

    if mode == "summarize":
        compressed = _summarize(text)
    else:  # compress mode
        compressed = _compress(text)

    compressed_tokens = estimate_tokens(compressed)
    savings = max(0, original_tokens - compressed_tokens)

    # Generate MCP reference for recovery (hash of original for deterministic lookup)
    mcp_reference = _generate_mcp_reference(text) if savings > 0 else None

    return CompressionResult(
        original_text=text,
        compressed_text=compressed,
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        savings=savings,
        mcp_reference=mcp_reference,
    )


def _compress(text: str) -> str:
    """
    Deterministic "caveman-style" compression:
    - Remove redundant whitespace
    - Abbreviate common verbose phrases
    - Preserve key identifiers, numbers, and structure
    """
    if not text:
        return text

    # Normalize whitespace
    result = re.sub(r'\s+', ' ', text.strip())

    # Abbreviation rules (deterministic, ordered)
    abbreviations = [
        # Code patterns
        (r'\bfunction\b', 'fn'),
        (r'\bvariable\b', 'var'),
        (r'\bconstant\b', 'const'),
        (r'\bparameter\b', 'param'),
        (r'\bargument\b', 'arg'),
        (r'\breturn\b', 'ret'),
        (r'\bimport\b', 'imp'),
        (r'\bexport\b', 'exp'),
        (r'\bdefault\b', 'def'),
        (r'\basync\b', 'async'),
        (r'\bawait\b', 'await'),
        # Common words
        (r'\bconfiguration\b', 'config'),
        (r'\binitialization\b', 'init'),
        (r'\bimplementation\b', 'impl'),
        (r'\bapplication\b', 'app'),
        (r'\bdirectory\b', 'dir'),
        (r'\blibrary\b', 'lib'),
        (r'\bmodule\b', 'mod'),
        (r'\bpackage\b', 'pkg'),
        (r'\bcomponent\b', 'comp'),
        (r'\binterface\b', 'iface'),
        (r'\bexception\b', 'exc'),
        (r'\benvironment\b', 'env'),
        (r'\bproduction\b', 'prod'),
        (r'\bdevelopment\b', 'dev'),
        (r'\btesting\b', 'test'),
        (r'\bdocumentation\b', 'docs'),
        (r'\brequirements\b', 'reqs'),
        (r'\bdependencies\b', 'deps'),
        # Verbose phrases
        (r'\bin order to\b', 'to'),
        (r'\bdue to the fact that\b', 'because'),
        (r'\bat this point in time\b', 'now'),
        (r'\bfor the purpose of\b', 'for'),
        (r'\bwith regard to\b', 're'),
        (r'\bas a matter of fact\b', 'actually'),
        (r'\bplease note that\b', 'note'),
        (r'\bit should be noted that\b', 'note'),
    ]

    for pattern, replacement in abbreviations:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # Remove filler words (deterministic list)
    filler_words = {
        'actually', 'basically', 'literally', 'really', 'very', 'quite',
        'somewhat', 'rather', 'fairly', 'pretty', 'simply', 'just',
        'merely', 'only', 'even', 'still', 'yet', 'already',
    }
    words = result.split()
    filtered = [w for w in words if w.lower() not in filler_words]
    result = ' '.join(filtered)

    # Collapse multiple spaces
    result = re.sub(r'\s+', ' ', result).strip()

    return result


def _summarize(text: str) -> str:
    """
    Deterministic summarization: extract first sentence + key identifiers.
    """
    if not text:
        return text

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if not sentences:
        return text

    # Take first sentence
    first = sentences[0]

    # Extract key identifiers (camelCase, snake_case, UPPER_CASE, file paths, URLs)
    identifiers = re.findall(r'\b[a-z]+(?:[A-Z][a-z]*)+\b|\b[A-Z_]+\b|\b[a-z_]+(?:_[a-z]+)+\b|\S*\.\w{2,4}\b', text)
    unique_identifiers = []
    seen = set()
    for ident in identifiers:
        if ident.lower() not in seen and len(ident) > 2:
            seen.add(ident.lower())
            unique_identifiers.append(ident)

    # Extract numbers
    numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)

    parts = [first]
    if unique_identifiers:
        parts.append('Key: ' + ', '.join(unique_identifiers[:10]))
    if numbers:
        parts.append('Numbers: ' + ', '.join(numbers[:5]))

    return ' | '.join(parts)


def _generate_mcp_reference(text: str) -> str:
    """
    Generate deterministic MCP recovery reference.
    Uses hash of original text for lookup key.
    """
    hash_obj = hashlib.sha256(text.encode('utf-8'))
    return f"mcp:{hash_obj.hexdigest()[:16]}"


def compress_request_text(
    text: str,
    mode: str = "compress",
    provider: str = "openai-compatible",
    model: str = "gpt-4",
) -> dict:
    """
    Compress request text and return structured result for API.

    Args:
        text: Input text to compress
        mode: Compression mode (compress, summarize, off)
        provider: LLM provider name
        model: Model name

    Returns:
        Dict with compression results ready for request creation
    """
    result = compress_text(text, mode)

    return {
        "input_tokens": result.original_tokens,
        "output_tokens": 0,  # Will be filled by caller after LLM response
        "compressed_tokens": result.compressed_tokens,
        "recovered_tokens": 0,
        "savings": result.savings,
        "mcp_recovery_used": result.mcp_reference is not None,
        "mcp_reference": result.mcp_reference,
        "compressed_text": result.compressed_text,
    }

