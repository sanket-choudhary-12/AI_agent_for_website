# AI Voice Web Agent

This project is a Python-based AI agent that provides a voice-controlled interface for navigating and interacting with a website. It uses web automation, speech recognition, and a Large Language Model (LLM) to create an intelligent conversational assistant that is context-aware of the content on the current webpage.

 <!-- Optional: Add a screenshot of the GUI and browser running -->

---

## Features

-   **Push-to-Talk Voice Control:** A simple `tkinter` GUI with a "Hold to Talk" button (and spacebar binding) for intuitive voice commands.
-   **Intelligent Web Navigation:** Understands natural language commands to navigate to different pages of a website (e.g., "Go to the career page").
-   **Context-Aware AI:** Utilizes the Groq API (with the Llama 3.3 model) to provide intelligent responses based on the content of the current webpage.
-   **Dynamic Information Extraction:** Scrapes the live webpage to find specific details like job listings, which are then fed to the AI for more accurate answers.
-   **Task-Oriented Actions:** Can perform tasks like finding a specific job on a careers page and initiating the application process.
-   **Natural Voice Feedback:** Uses the built-in macOS `say` command for clear, low-latency text-to-speech responses.

---

## Core Technologies

-   **Backend:** Python 3
-   **Speech Recognition:** `speechrecognition` (with Google Web Speech API)
-   **Web Automation:** `selenium`
-   **HTML Parsing:** `beautifulsoup4`
-   **AI / LLM:** Groq API (Llama 3.3 Model)
-   **GUI:** `tkinter`
-   **Concurrency:** `threading`

---

## Setup and Installation

### Prerequisites

-   Python 3.8+
-   Google Chrome browser installed
-   `chromedriver` (The script attempts to find it, but you may need to ensure it's in your system's PATH)
-   (On macOS) Access to microphone and system `say` command.

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Install Dependencies

It is recommended to use a virtual environment to manage dependencies.

```bash
# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install the required packages
pip install -r requirements.txt
```

### 3. Configure API Key

This agent requires a free API key from Groq to function.

1.  **Get a key:** Sign up for a free account at [GroqCloud](https://console.groq.com/keys) and create an API key.
2.  **Set the key:** You can set the API key in one of two ways:

    **a) Environment Variable (Recommended):**
    ```bash
    # On macOS/Linux
    export GROQ_API_KEY='your_gsk_..._api_key'

    # On Windows (Command Prompt)
    set GROQ_API_KEY="your_gsk_..._api_key"
    ```

    **b) Manual Input:** If you run the script without setting the environment variable, it will prompt you to enter the key in the console.

---

## How to Run the Agent

Once the setup is complete, run the main script from your terminal:

```bash
python your_script_name.py
```

The script will:
1.  Verify the Groq API connection.
2.  Launch a new Google Chrome window and navigate to the target website.
3.  Open a small "Voice Control" GUI window.

## How to Use

1.  The agent will greet you once it's ready.
2.  **Press and hold** the "🎤 Hold to Talk" button or the **SPACE bar** on your keyboard to speak a command.
3.  Release the button or key when you are finished speaking.
4.  The agent will process your command, perform any necessary actions in the browser, and respond verbally.

**Example Commands:**
-   "Tell me about the company's services."
-   "Navigate to the career page."
-   "Are there any AI intern positions available?"
-   "I want to apply for the developer job."
-   "Stop" or "Exit" to terminate the agent.
