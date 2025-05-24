class AIModelAdapter:
    def send_request(self, prompt: str, jd_text: str, cvs_texts: list[str]) -> dict:
        raise NotImplementedError("send_request must be implemented by subclasses")
