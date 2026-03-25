import random
from typing import Generator, Iterator
from backend.src.app.platform.guardrails.service import GuardrailService

# Available streaming modes
STREAMING_DISABLED = "streaming_disabled"
STREAMING_BUFFERED_START = "streaming_buffered_start"
STREAMING_FULL_GUARDED = "streaming_full_guarded"
STREAMING_UNRESTRICTED = "streaming_unrestricted"

DEFAULT_UX_MESSAGES = [
    "Interpretando tu consulta...",
    "Consultando la base de conocimiento...",
    "Procesando la información...",
    "Preparando una respuesta segura...",
]


class StreamingGuard:
    """
    Wraps an LLM token stream with configurable safety modes.

    Modes:
        streaming_disabled       - Buffer entire response, validate, return at once.
        streaming_buffered_start - Accumulate N chars, validate, then stream freely.
        streaming_full_guarded   - Validate every sliding window throughout the stream.
        streaming_unrestricted   - Pass tokens directly, no interception (non-sensitive environments).
    """

    def __init__(
        self,
        guardrail: GuardrailService,
        mode: str = STREAMING_BUFFERED_START,
        buffer_chars: int = 300,
        ux_messages: list[str] | None = None,
        blocked_response: str = "Por seguridad, no puedo completar esta respuesta.",
    ):
        self.guardrail = guardrail
        self.mode = mode
        self.buffer_chars = buffer_chars
        self.ux_messages = ux_messages or DEFAULT_UX_MESSAGES
        self.blocked_response = blocked_response

    def get_ux_placeholder(self) -> str:
        """Returns a random, safe, predefined UX message for the waiting period."""
        return random.choice(self.ux_messages)

    def _is_safe(self, text: str) -> bool:
        """Fail-closed wrapper: any exception → treat as unsafe."""
        try:
            is_safe, _ = self.guardrail.is_safe_message(text)
            return is_safe
        except Exception as e:
            print(f"⚠️ StreamingGuard: guardrail check failed ({e}). Applying fail-closed policy.")
            return False

    def wrap(self, token_stream: Iterator[str]) -> Generator[str, None, None]:
        """
        Main entry point. Delegates to the appropriate mode handler.
        """
        if self.mode == STREAMING_DISABLED:
            yield from self._mode_disabled(token_stream)
        elif self.mode == STREAMING_BUFFERED_START:
            yield from self._mode_buffered_start(token_stream)
        elif self.mode == STREAMING_FULL_GUARDED:
            yield from self._mode_full_guarded(token_stream)
        else:
            # streaming_unrestricted: pass-through
            yield from token_stream

    # ─── Mode Implementations ──────────────────────────────────────────────────

    def _mode_disabled(self, token_stream: Iterator[str]) -> Generator[str, None, None]:
        """
        Collect all tokens internally, validate the complete response,
        then yield it as a single chunk. No partial content ever reaches the client.
        """
        full_response = "".join(token_stream)

        if self._is_safe(full_response):
            yield full_response
        else:
            print("🛑 StreamingGuard [disabled mode]: full response blocked.")
            yield self.blocked_response

    def _mode_buffered_start(self, token_stream: Iterator[str]) -> Generator[str, None, None]:
        """
        Accumulate an initial buffer of N characters while the client sees a
        safe UX placeholder. Once the buffer is full, validate it:
          - If safe → release the buffer and stream the rest freely.
          - If unsafe → kill-switch: yield blocked_response instead.
        """
        buffer = ""
        buffer_released = False

        for token in token_stream:
            if not buffer_released:
                buffer += token
                if len(buffer) >= self.buffer_chars:
                    # Buffer is full — time to validate
                    if self._is_safe(buffer):
                        buffer_released = True
                        yield buffer   # Release the accumulated, validated buffer
                    else:
                        print("🛑 StreamingGuard [buffered_start]: kill-switch activated.")
                        yield self.blocked_response
                        return         # Stop the generator — nothing more reaches the client
                # Buffer still accumulating: nothing yielded yet (client sees UX message)
            else:
                # Buffer already released and validated: stream normally
                yield token

        # Handle edge case: stream ended before buffer reached threshold
        if not buffer_released and buffer:
            if self._is_safe(buffer):
                yield buffer
            else:
                print("🛑 StreamingGuard [buffered_start]: short response blocked.")
                yield self.blocked_response

    def _mode_full_guarded(self, token_stream: Iterator[str]) -> Generator[str, None, None]:
        """
        Sliding-window validation throughout the ENTIRE response.
        Every N characters, re-validate the accumulated text.
        If at any point the guardrail fires → kill-switch.

        Note: This mode adds latency. Recommended only for highest-sensitivity domains.
        """
        accumulated = ""
        window_buffer = ""
        last_validated_len = 0

        for token in token_stream:
            accumulated += token
            window_buffer += token

            # Check every buffer_chars window
            if len(accumulated) - last_validated_len >= self.buffer_chars:
                if not self._is_safe(accumulated):
                    print("🛑 StreamingGuard [full_guarded]: kill-switch activated mid-stream.")
                    yield self.blocked_response
                    return
                # Safe: release the window
                yield window_buffer
                window_buffer = ""
                last_validated_len = len(accumulated)

        # Flush any remaining tokens in the last (smaller) window
        if window_buffer:
            if self._is_safe(accumulated):
                yield window_buffer
            else:
                print("🛑 StreamingGuard [full_guarded]: final window blocked.")
                yield self.blocked_response
