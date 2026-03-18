"""
LLM Provider Abstraction
Provides a unified interface for Ollama and Claude API models.
"""

import os
import json
import requests
from abc import ABC, abstractmethod
from typing import Generator, Any

# Check if anthropic is available
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# Check if google-generativeai is available
try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def chat_stream(
        self,
        messages: list[dict],
        tools: list[dict],
        model: str,
        system_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs
    ) -> Generator[tuple[str, dict | None], None, None]:
        """
        Stream a chat response from the LLM.

        Yields:
            Tuple of (content_chunk, final_message)
            - During streaming: (chunk_text, None)
            - At the end: (None, final_message_dict)
        """
        pass

    @abstractmethod
    def format_tools(self, tools: list[dict]) -> list[dict]:
        """Convert tools to provider-specific format."""
        pass

    @abstractmethod
    def get_available_models(self) -> list[str]:
        """Get list of available models for this provider."""
        pass

    @abstractmethod
    def extract_tool_calls(self, response: dict) -> list[dict]:
        """Extract tool calls from response in a unified format."""
        pass


class OllamaProvider(LLMProvider):
    """Provider for Ollama models (both native and OpenAI-compatible modes)."""

    def __init__(self, base_url: str = None, api_flavor: str = None):
        """
        Initialize Ollama provider.

        Args:
            base_url: Ollama server URL (default: from env or localhost:11434)
            api_flavor: 'native' or 'openai' (default: auto-detect from URL)
        """
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        api_flavor = api_flavor or os.getenv("OLLAMA_API_FLAVOR", "").strip().lower()

        # Normalize URL (remove trailing endpoint paths)
        for suffix in ["/api/chat", "/api/tags", "/v1/chat/completions", "/v1/models"]:
            if self.base_url.endswith(suffix):
                self.base_url = self.base_url[:-len(suffix)]

        # Determine API mode
        if self.base_url.endswith("/v1") or api_flavor == "openai":
            self.api_mode = "openai"
            self.chat_url = f"{self.base_url}/chat/completions"
            self.tags_url = f"{self.base_url}/models"
        elif self.base_url.endswith("/api") or api_flavor == "native":
            self.api_mode = "native"
            self.chat_url = f"{self.base_url}/chat"
            self.tags_url = f"{self.base_url}/tags"
        else:
            self.api_mode = "native"
            self.chat_url = f"{self.base_url}/api/chat"
            self.tags_url = f"{self.base_url}/api/tags"

    def chat_stream(
        self,
        messages: list[dict],
        tools: list[dict],
        model: str,
        system_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs
    ) -> Generator[tuple[str, dict | None], None, None]:
        """Stream chat response from Ollama."""
        # Build messages with system prompt
        full_messages = [{"role": "system", "content": system_prompt}]
        for m in messages:
            if m.get("role") == "system":
                continue
            msg_copy = m.copy()
            if "content_for_model" in msg_copy:
                msg_copy["content"] = msg_copy.pop("content_for_model")
            full_messages.append(msg_copy)

        if self.api_mode == "openai":
            payload = {
                "model": model,
                "messages": full_messages,
                "tools": tools,
                "stream": True,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            yield from self._openai_stream(payload)
        else:
            payload = {
                "model": model,
                "messages": full_messages,
                "tools": tools,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }
            yield from self._native_stream(payload)

    def _native_stream(self, payload: dict) -> Generator[tuple[str, dict | None], None, None]:
        """Stream from native Ollama API."""
        final_message = {}
        yielded = False

        with requests.post(self.chat_url, json=payload, stream=True, timeout=120) as response:
            response.raise_for_status()
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                data = json.loads(line)
                if data.get("error"):
                    raise RuntimeError(data["error"])
                message = data.get("message", {})
                if message:
                    if message.get("tool_calls"):
                        final_message["tool_calls"] = message["tool_calls"]
                    if message.get("content") is not None:
                        final_message["content"] = message["content"]
                    if message.get("role"):
                        final_message["role"] = message["role"]
                content = message.get("content")
                if content:
                    yielded = True
                    yield content, final_message
                if data.get("done"):
                    break

        if not yielded:
            yield "", final_message

    def _openai_stream(self, payload: dict) -> Generator[tuple[str, dict | None], None, None]:
        """Stream from OpenAI-compatible API."""
        final_message = {"role": "assistant"}
        yielded = False
        content_buffer = ""
        tool_calls_buffer = {}

        with requests.post(self.chat_url, json=payload, stream=True, timeout=120) as response:
            response.raise_for_status()
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if not line.startswith("data:"):
                    continue
                data_str = line.split("data:", 1)[1].strip()
                if data_str == "[DONE]":
                    break
                data = json.loads(data_str)
                if data.get("error"):
                    raise RuntimeError(data["error"])
                choice = data.get("choices", [{}])[0]
                delta = choice.get("delta", {})

                if delta.get("content"):
                    content_buffer += delta["content"]
                    final_message["content"] = content_buffer
                    yielded = True
                    yield delta["content"], final_message

                for tool_call in delta.get("tool_calls", []) or []:
                    index = tool_call.get("index", 0)
                    entry = tool_calls_buffer.setdefault(
                        index,
                        {"id": None, "type": tool_call.get("type", "function"), "function": {"name": "", "arguments": ""}},
                    )
                    if tool_call.get("id"):
                        entry["id"] = tool_call["id"]
                    func_delta = tool_call.get("function", {})
                    if func_delta.get("name"):
                        entry["function"]["name"] += func_delta["name"]
                    if func_delta.get("arguments"):
                        entry["function"]["arguments"] += func_delta["arguments"]
                    final_message["tool_calls"] = list(tool_calls_buffer.values())

            if "tool_calls" in final_message and not yielded:
                yield "", final_message

    def format_tools(self, tools: list[dict]) -> list[dict]:
        """Ollama uses OpenAI-compatible tool format."""
        return tools

    def get_available_models(self) -> list[str]:
        """Fetch available models from Ollama server."""
        try:
            response = requests.get(self.tags_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if self.api_mode == "openai":
                # OpenAI format: {"data": [{"id": "model_name"}, ...]}
                models = data.get("data", [])
                return [m.get("id") for m in models if m.get("id")]
            else:
                # Native format: {"models": [{"name": "model_name"}, ...]}
                models = data.get("models", [])
                return [m.get("name") for m in models if m.get("name")]
        except Exception as e:
            print(f"Error fetching Ollama models: {e}")
            return []

    def extract_tool_calls(self, response: dict) -> list[dict]:
        """Extract tool calls from Ollama response."""
        tool_calls = response.get("tool_calls", []) or []
        unified = []
        for tc in tool_calls:
            func = tc.get("function", {})
            args = func.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            unified.append({
                "id": tc.get("id", f"tool_{len(unified)}"),
                "name": func.get("name"),
                "arguments": args,
            })
        return unified

    def is_connected(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            response = requests.get(self.tags_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False


class ClaudeProvider(LLMProvider):
    """Provider for Anthropic Claude API."""

    # Claude model name mapping (friendly name -> API model ID)
    MODEL_MAP = {
        "claude-opus-4-5": "claude-opus-4-5-20250514",
        "claude-sonnet-4": "claude-sonnet-4-20250514",
        "claude-haiku": "claude-haiku-4-20250414",
    }

    def __init__(self, api_key: str = None):
        """
        Initialize Claude provider.

        Args:
            api_key: Anthropic API key (default: from ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._client = None

    @property
    def client(self):
        """Lazy-initialize the Anthropic client."""
        if self._client is None:
            if not ANTHROPIC_AVAILABLE:
                raise RuntimeError("anthropic package is not installed. Run: pip install anthropic")
            if not self.api_key:
                raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set")
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def chat_stream(
        self,
        messages: list[dict],
        tools: list[dict],
        model: str,
        system_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs
    ) -> Generator[tuple[str, dict | None], None, None]:
        """Stream chat response from Claude API."""
        # Resolve model name
        api_model = self.MODEL_MAP.get(model, model)

        # Convert messages to Claude format
        claude_messages = self._convert_messages(messages)

        # Convert tools to Claude format
        claude_tools = self.format_tools(tools)

        # Prepare request kwargs
        request_kwargs = {
            "model": api_model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": claude_messages,
        }

        # Only add tools if there are any
        if claude_tools:
            request_kwargs["tools"] = claude_tools

        # Stream the response
        content_buffer = ""
        final_message = {"role": "assistant", "content": [], "tool_calls": []}

        with self.client.messages.stream(**request_kwargs) as stream:
            for event in stream:
                if event.type == "content_block_delta":
                    if hasattr(event.delta, "text"):
                        text = event.delta.text
                        content_buffer += text
                        yield text, None
                    elif hasattr(event.delta, "partial_json"):
                        # Tool input being streamed
                        pass

            # Get final message
            response = stream.get_final_message()

            # Process content blocks
            text_content = ""
            for block in response.content:
                if block.type == "text":
                    text_content = block.text
                elif block.type == "tool_use":
                    final_message["tool_calls"].append({
                        "id": block.id,
                        "name": block.name,
                        "arguments": block.input,
                    })

            final_message["content"] = text_content
            final_message["stop_reason"] = response.stop_reason

        # Yield final message
        yield "", final_message

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        """
        Convert messages to Claude format.

        Claude API requires:
        - Assistant messages with tool_use blocks must be followed by
          user messages with corresponding tool_result blocks
        - tool_result must reference tool_use IDs from the immediately
          preceding assistant message
        """
        claude_messages = []
        i = 0

        while i < len(messages):
            msg = messages[i]
            role = msg.get("role")
            content = msg.get("content_for_model", msg.get("content", ""))

            if role == "system":
                i += 1
                continue

            elif role == "user":
                claude_messages.append({"role": "user", "content": content})
                i += 1

            elif role == "assistant":
                # Check if this assistant message has tool_calls metadata
                tool_calls = msg.get("tool_calls", [])

                if tool_calls:
                    # Build content blocks: text + tool_use blocks
                    content_blocks = []
                    if content and content.strip():
                        content_blocks.append({"type": "text", "text": content})

                    for tc in tool_calls:
                        content_blocks.append({
                            "type": "tool_use",
                            "id": tc.get("id"),
                            "name": tc.get("name"),
                            "input": tc.get("arguments", {}),
                        })

                    claude_messages.append({"role": "assistant", "content": content_blocks})
                else:
                    # No tool calls, just text content
                    claude_messages.append({"role": "assistant", "content": content})
                i += 1

            elif role == "tool":
                # Collect all consecutive tool results into one user message
                tool_results = []
                while i < len(messages) and messages[i].get("role") == "tool":
                    tool_msg = messages[i]
                    tool_call_id = tool_msg.get("tool_call_id", "")
                    tool_content = tool_msg.get("content", "")

                    # Parse the content if it's JSON
                    try:
                        result_content = json.loads(tool_content) if isinstance(tool_content, str) else tool_content
                    except json.JSONDecodeError:
                        result_content = tool_content

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call_id,
                        "content": json.dumps(result_content) if isinstance(result_content, dict) else str(result_content),
                    })
                    i += 1

                claude_messages.append({"role": "user", "content": tool_results})
            else:
                i += 1

        return claude_messages

    def format_tools(self, tools: list[dict]) -> list[dict]:
        """Convert OpenAI-style tools to Claude format."""
        claude_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                claude_tools.append({
                    "name": func.get("name"),
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                })
        return claude_tools

    def get_available_models(self) -> list[str]:
        """Return available Claude models."""
        return list(self.MODEL_MAP.keys())

    def extract_tool_calls(self, response: dict) -> list[dict]:
        """Extract tool calls from Claude response (already in unified format)."""
        return response.get("tool_calls", [])

    def is_connected(self) -> bool:
        """Check if Claude API is available (API key is set)."""
        return bool(self.api_key)

    def get_masked_api_key(self) -> str:
        """Return masked API key for display."""
        if not self.api_key:
            return "Not set"
        return "••••••••••••••••"


class GeminiProvider(LLMProvider):
    """Provider for Google Gemini API."""

    # Gemini model name mapping (friendly name -> API model ID)
    # Note: Gemini 1.5 models are retired. Gemini 2.0 retiring March 2026.
    MODEL_MAP = {
        # Gemini 3.1 Series (Latest - Preview)
        "gemini-3.1-pro-preview": "gemini-3.1-pro-preview",
        # Gemini 3 Series (Preview)
        "gemini-3-flash-preview": "gemini-3-flash-preview",
        "gemini-3-pro-preview": "gemini-3-pro-preview",
        # Gemini 2.5 Series (Stable)
        "gemini-2.5-flash": "gemini-2.5-flash",
        "gemini-2.5-pro": "gemini-2.5-pro",
        "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
        # Gemini 2.0 Series (Retiring March 2026)
        "gemini-2.0-flash": "gemini-2.0-flash",
        "gemini-2.0-flash-lite": "gemini-2.0-flash-lite",
    }

    def __init__(self, api_key: str = None):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google API key (default: from GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._client = None

    @property
    def client(self):
        """Lazy-initialize the Gemini client."""
        if self._client is None:
            if not GOOGLE_AVAILABLE:
                raise RuntimeError("google-generativeai package is not installed. Run: pip install google-generativeai")
            if not self.api_key:
                raise RuntimeError("GEMINI_API_KEY environment variable is not set")
            genai.configure(api_key=self.api_key)
            self._client = genai
        return self._client

    def chat_stream(
        self,
        messages: list[dict],
        tools: list[dict],
        model: str,
        system_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs
    ) -> Generator[tuple[str, dict | None], None, None]:
        """Stream chat response from Gemini API."""
        # Resolve model name
        api_model = self.MODEL_MAP.get(model, model)

        # Convert messages to Gemini format
        gemini_contents = self._convert_messages(messages)

        # Convert tools to Gemini format
        gemini_tools = self.format_tools(tools)

        # Create the model with system instruction
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        model_instance = self.client.GenerativeModel(
            model_name=api_model,
            system_instruction=system_prompt,
            generation_config=generation_config,
            tools=gemini_tools if gemini_tools else None,
        )

        # Start chat and stream response
        # Gemini requires us to send messages, so we need to handle the history carefully
        content_buffer = ""
        final_message = {"role": "assistant", "content": "", "tool_calls": []}

        # Determine what to send based on the last message type
        if not gemini_contents:
            # No messages, send empty
            history = []
            last_message = " "  # Gemini requires non-empty content
        else:
            last_content = gemini_contents[-1]
            last_parts = last_content.get("parts", [])

            # Check if the last message contains function_response (tool result)
            has_function_response = any(
                isinstance(p, dict) and "function_response" in p
                for p in last_parts
            )

            if has_function_response:
                # Last message is a tool result - include all messages in history
                # and send a prompt asking to continue
                history = gemini_contents
                last_message = "Please analyze the tool result above and provide a response."
            else:
                # Last message is a regular user message
                history = gemini_contents[:-1] if len(gemini_contents) > 1 else []
                # Extract text from the last message
                last_text = ""
                for part in last_parts:
                    if isinstance(part, dict) and "text" in part:
                        last_text = part["text"]
                        break
                last_message = last_text if last_text else " "

        chat = model_instance.start_chat(history=history)

        try:
            # Try streaming first
            response = chat.send_message(last_message, stream=True)

            for chunk in response:
                # Handle text content - check if text exists and is not empty
                try:
                    if hasattr(chunk, 'text') and chunk.text:
                        content_buffer += chunk.text
                        yield chunk.text, None
                except ValueError:
                    # chunk.text raises ValueError when the response contains function calls
                    # This is expected behavior - continue to process function calls below
                    pass

            # Get final response for tool calls after streaming completes
            # Check if there are function calls in the response
            if hasattr(response, '_result') and response._result.candidates:
                candidate = response._result.candidates[0]
                if hasattr(candidate, 'content') and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            fc = part.function_call
                            # Convert protobuf MapComposite to plain dict via JSON serialization
                            args = self._convert_args_to_dict(fc.args) if fc.args else {}
                            final_message["tool_calls"].append({
                                "id": f"call_{fc.name}_{len(final_message['tool_calls'])}",
                                "name": fc.name,
                                "arguments": args,
                            })

            final_message["content"] = content_buffer

        except Exception as e:
            # If streaming fails, try non-streaming
            try:
                response = chat.send_message(last_message, stream=False)

                # Process the response parts
                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        # Check for text content
                        if hasattr(part, 'text') and part.text:
                            final_message["content"] = part.text
                            yield part.text, None
                        # Check for function calls
                        elif hasattr(part, 'function_call') and part.function_call:
                            fc = part.function_call
                            # Convert protobuf MapComposite to plain dict via JSON serialization
                            args = self._convert_args_to_dict(fc.args) if fc.args else {}
                            final_message["tool_calls"].append({
                                "id": f"call_{fc.name}_{len(final_message['tool_calls'])}",
                                "name": fc.name,
                                "arguments": args,
                            })
            except Exception as inner_e:
                # Re-raise with more context
                raise RuntimeError(f"Gemini API error: {str(e)}. Fallback also failed: {str(inner_e)}")

        # Check if we got any content or tool calls - warn if empty
        if not final_message["content"] and not final_message["tool_calls"]:
            final_message["content"] = "[Gemini returned an empty response. This may be due to content filtering or an API issue. Please try rephrasing your request.]"

        # Yield final message
        yield "", final_message

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        """
        Convert messages to Gemini format.

        Gemini uses a different format:
        - role: "user" or "model"
        - parts: list of content parts

        Gemini requires strict alternation between user and model roles.
        Tool responses must be sent as user messages with function_response parts.
        """
        gemini_messages = []
        i = 0

        while i < len(messages):
            msg = messages[i]
            role = msg.get("role")
            content = msg.get("content_for_model", msg.get("content", ""))

            if role == "system":
                # System messages are handled via system_instruction
                i += 1
                continue

            elif role == "user":
                gemini_messages.append({
                    "role": "user",
                    "parts": [{"text": content if content else " "}]
                })
                i += 1

            elif role == "assistant":
                parts = []
                # Add text content if present
                if content and content.strip():
                    parts.append({"text": content})

                # Check if this assistant message has tool_calls
                tool_calls = msg.get("tool_calls", [])
                if tool_calls:
                    for tc in tool_calls:
                        # Add function call parts
                        parts.append({
                            "function_call": {
                                "name": tc.get("name"),
                                "args": tc.get("arguments", {})
                            }
                        })

                # Only add if there are parts
                if parts:
                    gemini_messages.append({
                        "role": "model",
                        "parts": parts
                    })
                else:
                    # Empty assistant message - add placeholder
                    gemini_messages.append({
                        "role": "model",
                        "parts": [{"text": " "}]
                    })
                i += 1

            elif role == "tool":
                # Collect all consecutive tool results
                function_responses = []
                while i < len(messages) and messages[i].get("role") == "tool":
                    tool_msg = messages[i]
                    tool_content = tool_msg.get("content", "")
                    tool_name = tool_msg.get("tool_call_id", "tool")

                    # Try to parse JSON content
                    try:
                        if isinstance(tool_content, str):
                            parsed = json.loads(tool_content)
                        else:
                            parsed = tool_content
                    except (json.JSONDecodeError, TypeError):
                        parsed = {"result": tool_content}

                    function_responses.append({
                        "function_response": {
                            "name": tool_name,
                            "response": parsed if isinstance(parsed, dict) else {"result": str(parsed)}
                        }
                    })
                    i += 1

                if function_responses:
                    gemini_messages.append({
                        "role": "user",
                        "parts": function_responses
                    })
            else:
                i += 1

        return gemini_messages

    def _convert_args_to_dict(self, args) -> dict:
        """
        Convert Gemini's protobuf MapComposite/Struct to a plain Python dict.

        Gemini returns function call arguments as protobuf objects that can't be
        deep-copied. This method converts them to plain dicts via JSON serialization.
        """
        if args is None:
            return {}

        try:
            # Try to convert via type_pb2.Struct if available
            if hasattr(args, 'items'):
                # It's dict-like, convert recursively
                result = {}
                for key, value in args.items():
                    result[key] = self._convert_value(value)
                # Post-process to parse string-encoded arrays/objects
                result = self._parse_string_encoded_values(result)
                return result
            else:
                # Try JSON serialization as fallback
                result = json.loads(json.dumps(dict(args), default=str))
                return self._parse_string_encoded_values(result)
        except Exception:
            # Last resort: simple dict conversion
            try:
                return dict(args)
            except Exception:
                return {}

    def _parse_string_encoded_values(self, d: dict) -> dict:
        """
        Parse string-encoded JSON values (arrays, objects) back to Python types.

        Gemini sometimes returns arrays as strings like "[1, 2, 3]" instead of actual arrays.
        """
        result = {}
        for key, value in d.items():
            if isinstance(value, str):
                # Check if it looks like a JSON array or object
                stripped = value.strip()
                if (stripped.startswith('[') and stripped.endswith(']')) or \
                   (stripped.startswith('{') and stripped.endswith('}')):
                    try:
                        parsed = json.loads(stripped)
                        result[key] = parsed
                        continue
                    except json.JSONDecodeError:
                        pass
            result[key] = value
        return result

    def _convert_value(self, value):
        """Recursively convert protobuf values to Python types."""
        if value is None:
            return None
        elif isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, (list, tuple)):
            return [self._convert_value(v) for v in value]
        elif hasattr(value, 'items'):
            # Dict-like (protobuf Struct/MapComposite)
            return {k: self._convert_value(v) for k, v in value.items()}
        elif hasattr(value, '__iter__'):
            # Iterable but not string/dict - likely protobuf RepeatedComposite (array)
            try:
                return [self._convert_value(v) for v in value]
            except Exception:
                return str(value)
        else:
            # Try to convert to appropriate type
            try:
                # Check if it's a number
                if hasattr(value, 'number_value'):
                    return value.number_value
                elif hasattr(value, 'string_value'):
                    return value.string_value
                elif hasattr(value, 'bool_value'):
                    return value.bool_value
                elif hasattr(value, 'list_value'):
                    return [self._convert_value(v) for v in value.list_value.values]
                else:
                    return str(value)
            except Exception:
                return str(value)

    def format_tools(self, tools: list[dict]) -> list:
        """Convert OpenAI-style tools to Gemini format."""
        if not tools:
            return []

        gemini_tools = []
        function_declarations = []

        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                params = func.get("parameters", {"type": "object", "properties": {}})

                # Convert parameters to Gemini schema format
                gemini_params = self._convert_parameters(params)

                function_declarations.append({
                    "name": func.get("name"),
                    "description": func.get("description", ""),
                    "parameters": gemini_params,
                })

        if function_declarations:
            gemini_tools.append({"function_declarations": function_declarations})

        return gemini_tools

    def _convert_parameters(self, params: dict) -> dict:
        """Convert OpenAI parameters schema to Gemini format."""
        # Gemini uses a similar schema format but with some differences
        gemini_params = {
            "type": params.get("type", "object").upper(),
            "properties": {},
        }

        if "properties" in params:
            for prop_name, prop_def in params["properties"].items():
                prop_type = prop_def.get("type", "string").upper()
                gemini_prop = {"type": prop_type}

                if "description" in prop_def:
                    gemini_prop["description"] = prop_def["description"]

                if "enum" in prop_def:
                    gemini_prop["enum"] = prop_def["enum"]

                if prop_type == "ARRAY" and "items" in prop_def:
                    items = prop_def["items"]
                    gemini_prop["items"] = {"type": items.get("type", "string").upper()}

                gemini_params["properties"][prop_name] = gemini_prop

        if "required" in params:
            gemini_params["required"] = params["required"]

        return gemini_params

    def get_available_models(self) -> list[str]:
        """Return available Gemini models."""
        return list(self.MODEL_MAP.keys())

    def extract_tool_calls(self, response: dict) -> list[dict]:
        """Extract tool calls from Gemini response (already in unified format)."""
        return response.get("tool_calls", [])

    def is_connected(self) -> bool:
        """Check if Gemini API is available (API key is set)."""
        return bool(self.api_key)

    def get_masked_api_key(self) -> str:
        """Return masked API key for display."""
        if not self.api_key:
            return "Not set"
        return "••••••••••••••••"


def get_provider(provider_type: str, **kwargs) -> LLMProvider:
    """
    Factory function to get the appropriate provider.

    Args:
        provider_type: 'claude' or 'gemini' (Ollama disabled for container deployment)
        **kwargs: Provider-specific arguments

    Returns:
        LLMProvider instance
    """
    if provider_type.lower() == "claude":
        return ClaudeProvider(**kwargs)
    elif provider_type.lower() == "gemini":
        return GeminiProvider(**kwargs)
    elif provider_type.lower() == "ollama":
        return OllamaProvider(**kwargs)


def get_all_available_models() -> dict[str, list[str]]:
    """
    Get all available models from all providers.

    Returns:
        Dict mapping provider name to list of model names
    """
    models = {}

    # Ollama disabled for container deployment
    # models["Ollama"] = []

    # Claude models
    claude = ClaudeProvider()
    if claude.is_connected():
        models["Claude API"] = claude.get_available_models()
    else:
        models["Claude API"] = []

    # Gemini models
    gemini = GeminiProvider()
    if gemini.is_connected():
        models["Gemini API"] = gemini.get_available_models()
    else:
        models["Gemini API"] = []

    return models
