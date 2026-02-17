#!/usr/bin/env python3
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 7860))
    share = os.getenv("GRADIO_SHARE", "false").lower() == "true"
    debug = os.getenv("DEBUG_INVOICE", "false").lower() == "true"

    from ui.gradio_ui import build_gradio_ui
    demo = build_gradio_ui()

    # print ONLY the local URL, nothing else
    print(f"http://localhost:{port}")

    demo.launch(
        server_name=host,
        server_port=port,
        share=share,
        show_error=debug,
        quiet=True,           # keep terminal silent
        auth=None
    )

if __name__ == "__main__":
    main()
