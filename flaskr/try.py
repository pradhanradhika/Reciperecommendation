import threading
import time
import gradio as gr
import os
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv

from flaskr import app

# Load environment variables and configure Google API key
load_dotenv(find_dotenv())
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

model = genai.GenerativeModel()

# Handle user query function
def handle_user_query(msg, chatbot):
    print(msg, chatbot)
    chatbot += [[msg, None]]
    return '', chatbot

# Format chatbot history for API requests
def generate_chatbot(chatbot: list[list[str, str]]) -> list[list[str, str]]:
    formatted_chatbot = []
    if len(chatbot) == 0:
        return formatted_chatbot
    for ch in chatbot:
        formatted_chatbot.append(
            {
                "role": "user",
                "parts": [ch[0]]
            }
        )
        formatted_chatbot.append(
            {
                "role": "model",
                "parts": [ch[1]]
            }
        )
    return formatted_chatbot

# Handle response from the Gemini model
def handle_gemini_response(chatbot):
    query = chatbot[-1][0]
    formatted_chatbot = generate_chatbot(chatbot[:-1])
    chat = model.start_chat(history=formatted_chatbot)
    response = chat.send_message(query)
    chatbot[-1][1] = response.text
    return chatbot

# Define the Gradio interface
def create_gradio_interface():
    with gr.Blocks(css=".gradio-container {background-color: light green;} .chatbot .message-user {background-color: #87cefa; color: light blue;} .chatbot .message-bot {background-color: #e0ffff; color: light green;}") as demo:
        chatbot = gr.Chatbot(
            label='Chat with Gemini',
            bubble_full_width=False,
        )
        msg = gr.Textbox()
        clear = gr.ClearButton([msg, chatbot])
        msg.submit(
            handle_user_query,
            [msg, chatbot],
            [msg, chatbot]
        ).then(
            handle_gemini_response,
            [chatbot],
            [chatbot]
        )

    return demo

# Function to run Gradio in a separate thread
def run_gradio():
    demo = create_gradio_interface()
    #demo.queue()
    demo.launch(server_name="127.0.0.1", server_port=7860, share=True, prevent_thread_lock=True)

# Start the Gradio interface in a separate thread
if __name__ == "__main__":
    # Start Gradio in a daemon thread
    gradio_thread = threading.Thread(target=run_gradio, daemon=True)
    gradio_thread.start()

    # Wait for Gradio to start
    time.sleep(2)  # Ensure Gradio is initialized before starting Flask (adjust the time if needed)

    # Run Flask or other processes in the main thread
    app.run(port=5000)
