import base64
import json
import mimetypes
from pathlib import Path
import requests


class MistralError(Exception):
    pass


def image_url(path):
    path = Path(path)
    mime = mimetypes.guess_type(path.name)[0]
    
    if mime not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise MistralError("Choose a JPEG, PNG, WebP, or GIF image.")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


class Mistral:
    
    def __init__(self, key):
        self.key = key.strip()
        if not self.key:
            raise MistralError("Key not set")

    def post(self, endpoint, payload):
        try:
            response = requests.post(
                f"https://api.mistral.ai/v1/{endpoint}",
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                json=payload,
                timeout=120,
            )
            
        except requests.RequestException as error:
            raise MistralError(f"Couldnt reach Mistral: {error}") from error

        if not response.ok:
            try:
                body = response.json()
                detail = body.get("message") or body.get("detail") or response.text

            except ValueError:
                detail = response.text
            raise MistralError(f"request failed ({response.status_code}): {str(detail)[:500]}")

        try:
            return response.json()

        except ValueError as error:
            raise MistralError("Returned an invalid response.") from error

    def chat(self, content):
        result = self.post("chat/completions", {
            "model": "mistral-small-latest",
            "messages": [{"role": "user", "content": content}],
            "response_format": {"type": "json_object"},
        })
        
        try:
            content = result["choices"][0]["message"]["content"]
            data = json.loads(content)
            
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
            raise MistralError("unexpected chat responsoe error") from error
            
        if not isinstance(data, dict):
            raise MistralError("unexpected chat response error")
        return data

    def cover(self, path):
        result = self.chat([
            {"type": "text", "text": "I want you to identify the book on this cover. Return JSON with title and author as strings. Use an empty string if you are ever uncertain. Do not guess at all."},
            {"type": "image_url", "image_url": image_url(path)},
        ])
        return {
            "title": str(result.get("title") or ""),
            "author": str(result.get("author") or ""),
        }

    def ocr(self, path, pages=None):
        path = Path(path)
        if path.suffix.lower() == ".pdf":
            encoded = base64.b64encode(path.read_bytes()).decode('ascii')
            document = {"type": "document_url", "document_url": f"data:application/pdf;base64,{encoded}"}
        else:
            document = {"type": "image_url", "image_url": image_url(path)}
        request = {"model": "mistral-ocr-latest", "document": document}
        if pages is not None:
            request["pages"] = pages
        result = self.post("ocr", request)
        pages = result.get("pages")
        if not isinstance(pages, list):
            raise MistralError("unexpected OCR response.")
        text = "\n\n".join(str(page.get("markdown", "")) for page in pages).strip()
        if not text:
            raise MistralError("No text was found")
        return text

    def reel(self, topic, source=""):
        prompt = (
            "Create a short educational motion graphics script about the topic below. "
            "Return a JSON with 'title', 'category', 'caption', and 'slides' (an array of exactly 3 objects, "
            "each with 'headline' and 'body'). Headlines under 7 words, bodies under 25 words. "
            "Be specific, accurate and engaging. Do not invent quotations or cite sources you have not seen. "
            "If source text is provided, use it as context, not as a outright quotation.\n"
            f"Topic: {topic}\nSource text: {source[:12000]}"
        )
        result = self.chat(prompt)
        slides = result.get("slides")
        if not isinstance(slides, list):
            raise MistralError("The generated reel had no slides. Please try again.")
        slides = [
            {"headline": str(slide["headline"]), "body": str(slide["body"])}
            for slide in slides
            if isinstance(slide, dict) and slide.get("headline") and slide.get("body")
        ]
        if not slides:
            raise MistralError("generated reel had no usable slides. please try again.")
        return {
            "title": str(result.get("title") or topic),
            "category": str(result.get("category") or "IDEAS"),
            "caption": str(result.get("caption") or ""),
            "slides": slides[:5],
            "source": source,
            "demo": False,
        }

    def research(self, topic):
        result = self.post("conversations", {
            "model": "mistral-large-latest",
            "instructions": "Research the user's topic. Give a concise answer with source URLs. Distinguish uncertain things from factual things.",
            "tools": [{"type": "web_search"}],
            "inputs": topic,
            "store": False,
        })
        parts = []

        for output in result.get("outputs", []):
            if output.get("type") != "message.output":
                continue
            content = output.get("content", "")

            if isinstance(content, str):
                parts.append(content)

            elif isinstance(content, list):
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") == "text":
                        parts.append(item.get("text", ""))
                    elif item.get("type") == "reference":
                        parts.append(" [" + ", ".join(map(str, item.get("reference_ids", []))) + "] ")

        if not parts:
            raise MistralError("The research agent returned no text.")
        return "".join(parts)
