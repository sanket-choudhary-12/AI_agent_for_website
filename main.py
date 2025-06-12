import speech_recognition as sr
import subprocess
import time
import re
import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
import requests
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceControlGUI:
    def __init__(self, callback):
        self.callback = callback
        self.is_listening = False
        self.root = tk.Tk()
        self.root.title("Voice Control")
        self.root.geometry("300x150")
        self.root.attributes('-topmost', True)
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to listen", font=('Arial', 12))
        self.status_label.pack(pady=10)
        
        # Push to talk button
        self.talk_button = tk.Button(
            main_frame, 
            text="🎤 Hold to Talk",
            font=('Arial', 14, 'bold'),
            bg='#4CAF50',
            fg='white',
            activebackground='#45a049',
            relief='raised',
            bd=3,
            padx=20,
            pady=10
        )
        self.talk_button.pack(pady=10)
        
        # Bind mouse events
        self.talk_button.bind('<Button-1>', self.start_listening)
        self.talk_button.bind('<ButtonRelease-1>', self.stop_listening)
        
        # Bind keyboard events (space bar)
        self.root.bind('<KeyPress-space>', self.start_listening)
        self.root.bind('<KeyRelease-space>', self.stop_listening)
        self.root.focus_set()
        
        # Instructions
        instructions = ttk.Label(main_frame, text="Hold button or SPACE to talk", font=('Arial', 9))
        instructions.pack()
        
    def start_listening(self, event=None):
        if not self.is_listening:
            self.is_listening = True
            self.talk_button.config(text="🔴 Listening...", bg='#f44336')
            self.status_label.config(text="Listening... Speak now!")
            threading.Thread(target=self.callback, args=('start',), daemon=True).start()
    
    def stop_listening(self, event=None):
        if self.is_listening:
            self.is_listening = False
            self.talk_button.config(text="🎤 Hold to Talk", bg='#4CAF50')
            self.status_label.config(text="Processing...")
            threading.Thread(target=self.callback, args=('stop',), daemon=True).start()
    
    def update_status(self, status):
        self.status_label.config(text=status)
    
    def run(self):
        self.root.mainloop()

class AIVoiceWebAgent:
    def __init__(self):
        """Initialize the Enhanced AI Voice Web Agent"""
        self.website_url = "https://www.ikf.co.in/"
        self.driver = None
        self.listening = False
        self.current_page_content = ""
        self.conversation_history = []
        self.current_context = {}  # Store current context (jobs, forms, etc.)
        self.is_recording = False
        self.audio_data = None
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Use macOS built-in TTS
        self.use_macos_say = sys.platform == "darwin"
        
        # Groq API setup
        self.groq_api_key = None
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Website context
        self.website_context = {
            'company_name': 'I Knowledge Factory',
            'website_url': 'https://www.ikf.co.in/',
            'available_pages': ['home', 'about', 'services', 'career', 'contact', 'portfolio', 'blog', 'team'],
            'main_services': ['web development', 'mobile app development', 'digital marketing', 'IT consulting']
        }
        
        # Get API key first
        self.get_groq_api_key()
        
        # Setup GUI
        self.gui = VoiceControlGUI(self.handle_voice_control)
        
        # Calibrate microphone
        self.calibrate_microphone()

    def get_groq_api_key(self):
        """Get Groq API key from environment or prompt user"""
        api_key = os.getenv('GROQ_API_KEY')
        
        if not api_key:
            print("\n" + "="*50)
            print("GROQ API KEY REQUIRED")
            print("="*50)
            print("To use this AI agent, you need a free Groq API key.")
            print("1. Go to https://console.groq.com/keys")
            print("2. Sign up for free")
            print("3. Create an API key")
            print("4. Either:")
            print("   - Set environment variable: export GROQ_API_KEY='your_key'")
            print("   - Or enter it below")
            print("="*50)
            
            api_key = input("Enter your Groq API key: ").strip()
            if not api_key:
                print("No API key provided. Exiting...")
                sys.exit(1)
        
        if not api_key.startswith('gsk_'):
            print("Warning: API key doesn't start with 'gsk_'. Please verify it's correct.")
        
        self.groq_api_key = api_key
        print(f"✅ API key configured (ends with: ...{api_key[-8:]})")
        return api_key

    def test_groq_connection(self):
        """Test the Groq API connection with a simple request"""
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "user", "content": "Hello, can you respond with just 'Connection test successful'?"}
                ],
                "temperature": 0.1,
                "max_tokens": 20
            }
            
            response = requests.post(self.groq_url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Groq API connection successful!")
                return True
            else:
                print(f"❌ Groq API test failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Groq API connection error: {e}")
            return False

    def extract_detailed_page_content(self):
        """Extract detailed content from current page including job details, forms, etc."""
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            content = {
                'title': self.driver.title,
                'url': self.driver.current_url,
                'headings': [],
                'job_listings': [],
                'forms': [],
                'buttons': [],
                'main_content': '',
                'page_type': 'general'
            }
            
            # Get headings
            headings = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4")
            content['headings'] = [h.text.strip() for h in headings if h.text.strip()]
            
            # Check if this is a career page
            if 'career' in self.driver.current_url.lower():
                content['page_type'] = 'career'
                
                # Extract job listings
                job_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".job-listing, .career-item, .position, [class*='job'], [class*='position'], [class*='opening']")
                
                for job in job_elements:
                    job_info = {
                        'title': '',
                        'description': '',
                        'requirements': '',
                        'duration': '',
                        'location': '',
                        'element': job
                    }
                    
                    # Try to extract job title
                    title_elem = job.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, .title, .job-title")
                    if title_elem:
                        job_info['title'] = title_elem[0].text.strip()
                    
                    # Get job description/details
                    job_info['description'] = job.text.strip()
                    
                    if job_info['title'] or len(job_info['description']) > 20:
                        content['job_listings'].append(job_info)
                
                # Look for apply buttons or forms
                apply_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                    "button[class*='apply'], a[class*='apply'], .apply-btn, [href*='apply']")
                content['buttons'] = [{'text': btn.text.strip(), 'element': btn} for btn in apply_buttons]
            
            # Get forms
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            for form in forms:
                form_info = {
                    'inputs': [],
                    'element': form
                }
                inputs = form.find_elements(By.CSS_SELECTOR, "input, textarea, select")
                for inp in inputs:
                    form_info['inputs'].append({
                        'type': inp.get_attribute('type'),
                        'name': inp.get_attribute('name'),
                        'placeholder': inp.get_attribute('placeholder'),
                        'element': inp
                    })
                content['forms'].append(form_info)
            
            # Get main content
            body = self.driver.find_element(By.TAG_NAME, "body")
            content['main_content'] = body.text[:2000]
            
            self.current_page_content = content
            return content
            
        except Exception as e:
            print(f"⚠️ Error extracting detailed page content: {e}")
            return {'page_type': 'general', 'main_content': '', 'job_listings': [], 'forms': []}

    def get_ai_response(self, user_input, detailed_content=None):
        """Get intelligent response from Groq LLM with enhanced context"""
        try:
            if not detailed_content:
                detailed_content = self.extract_detailed_page_content()
            
            # Build enhanced context-aware prompt
            context_info = ""
            if detailed_content['page_type'] == 'career':
                context_info = f"""
CURRENT PAGE: Career page with job listings
AVAILABLE JOBS: {json.dumps([job['title'] + ': ' + job['description'][:200] for job in detailed_content['job_listings']], indent=2)}
APPLY BUTTONS AVAILABLE: {len(detailed_content['buttons']) > 0}
"""
            
            conversation_context = ""
            if self.conversation_history:
                recent_conv = self.conversation_history[-3:]
                conversation_context = f"RECENT CONVERSATION:\n{json.dumps(recent_conv, indent=2)}"
            
            system_prompt = f"""You are an intelligent voice assistant for the {self.website_context['company_name']} website.

ENHANCED CAPABILITIES:
- Answer questions about company, services, jobs with specific details from current page
- Navigate to different pages intelligently
- Help with job applications by finding specific jobs and application forms
- Remember conversation context and refer to previous discussions
- Extract and provide specific information from current page content

CURRENT PAGE DETAILS:
- URL: {detailed_content.get('url', 'unknown')}
- Page Type: {detailed_content.get('page_type', 'general')}
- Title: {detailed_content.get('title', '')}
- Main Headings: {', '.join(detailed_content.get('headings', [])[:3])}

{context_info}

{conversation_context}

IMPORTANT INSTRUCTIONS:
1. If user asks about specific jobs (like "AI LLM intern"), provide details from the job listings above
2. If user wants to apply for a job, guide them to the specific application process
3. Remember what we discussed before - refer to previous context
4. Be specific about job details (duration, requirements, etc.) when available
5. Keep responses conversational but informative (2-3 sentences max)
6. If you need to perform actions (navigate, click apply), mention them clearly

Current page content: {detailed_content.get('main_content', '')[:800]}"""

            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                "temperature": 0.7,
                "max_tokens": 400,
                "top_p": 1,
                "stream": False
            }
            
            response = requests.post(self.groq_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                
                # Store conversation with context
                self.conversation_history.append({
                    "user": user_input, 
                    "assistant": ai_response,
                    "page_context": detailed_content.get('page_type', 'general'),
                    "timestamp": time.time()
                })
                
                # Keep only last 8 conversations
                if len(self.conversation_history) > 8:
                    self.conversation_history = self.conversation_history[-8:]
                
                return ai_response
            else:
                print(f"Groq API error: {response.status_code}")
                print(f"Error details: {response.text}")
                return "I'm having trouble accessing my AI capabilities right now."
                
        except Exception as e:
            print(f"AI response error: {e}")
            return "I'm experiencing some technical difficulties."

    def extract_actions_from_response(self, ai_response, user_input):
        """Extract and prioritize actions from AI response and user input"""
        actions = []
        response_lower = ai_response.lower()
        user_lower = user_input.lower()
        
        # High priority: Direct job application requests
        if any(phrase in user_lower for phrase in ['apply for', 'want to apply', 'application']):
            # Check for specific job mentions
            job_keywords = ['ai', 'llm', 'intern', 'developer', 'designer', 'marketing']
            for keyword in job_keywords:
                if keyword in user_lower:
                    actions.append(("apply_for_job", keyword))
                    break
            
            if not any(action[0] == "apply_for_job" for action in actions):
                actions.append(("show_jobs", ""))
        
        # Navigation requests
        for page in self.website_context['available_pages']:
            if (f"navigate to {page}" in response_lower or f"go to {page}" in response_lower or 
                f"visit {page}" in response_lower or f"{page} page" in user_lower):
                actions.append(("navigate", page))
        
        # Context-specific actions
        if any(word in user_lower for word in ["career", "job", "position", "hiring", "opening"]):
            if "navigate" not in [action[0] for action in actions]:
                actions.append(("navigate", "career"))
        
        if any(word in user_lower for word in ["contact", "reach out", "get in touch"]):
            actions.append(("navigate", "contact"))
        
        if any(word in user_lower for word in ["service", "what we do", "offerings"]):
            actions.append(("navigate", "services"))
        
        if any(word in user_lower for word in ["portfolio", "work", "projects"]):
            actions.append(("navigate", "portfolio"))
        
        return actions

    def apply_for_job(self, job_keyword):
        """Handle job application process"""
        try:
            detailed_content = self.extract_detailed_page_content()
            
            # First, ensure we're on the career page
            if detailed_content['page_type'] != 'career':
                self.navigate_to_page('career')
                time.sleep(2)
                detailed_content = self.extract_detailed_page_content()
            
            # Find matching job
            target_job = None
            for job in detailed_content['job_listings']:
                if job_keyword.lower() in job['title'].lower() or job_keyword.lower() in job['description'].lower():
                    target_job = job
                    break
            
            if target_job:
                print(f"🎯 Found job: {target_job['title']}")
                
                # Try to click on the job or find apply button
                try:
                    # Scroll to job element
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", target_job['element'])
                    time.sleep(1)
                    
                    # Look for apply button near this job
                    apply_button = None
                    try:
                        apply_button = target_job['element'].find_element(By.CSS_SELECTOR, 
                            "button[class*='apply'], a[class*='apply'], .apply-btn, [href*='apply']")
                    except:
                        # Look for apply button in the general area
                        apply_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                            "button[class*='apply'], a[class*='apply'], .apply-btn, [href*='apply']")
                        if apply_buttons:
                            apply_button = apply_buttons[0]
                    
                    if apply_button:
                        print("🔘 Clicking apply button...")
                        apply_button.click()
                        time.sleep(2)
                        return True
                    else:
                        print("ℹ️ No apply button found, job details displayed")
                        return True
                        
                except Exception as e:
                    print(f"Error interacting with job element: {e}")
                    return False
            else:
                print(f"❌ Job with keyword '{job_keyword}' not found")
                return False
                
        except Exception as e:
            print(f"❌ Error in job application process: {e}")
            return False

    def handle_voice_control(self, action):
        """Handle voice control from GUI"""
        if action == 'start':
            self.start_recording()
        elif action == 'stop':
            self.stop_recording_and_process()

    def start_recording(self):
        """Start recording audio"""
        if not self.is_recording:
            self.is_recording = True
            try:
                with self.microphone as source:
                    print("🎤 Recording... Speak now!")
                    # Start listening in a separate thread
                    self.audio_data = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
            except Exception as e:
                print(f"Recording error: {e}")
                self.is_recording = False

    def stop_recording_and_process(self):
        """Stop recording and process the audio"""
        if self.is_recording and self.audio_data:
            self.is_recording = False
            try:
                print("🔄 Processing speech...")
                command = self.recognizer.recognize_google(self.audio_data).lower()
                print(f"👤 You said: '{command}'")
                
                # Update GUI
                self.gui.update_status("Processing command...")
                
                # Process the command
                self.process_command(command)
                
                # Reset GUI
                self.gui.update_status("Ready to listen")
                
            except sr.UnknownValueError:
                print("❌ Could not understand the audio")
                self.gui.update_status("Could not understand - try again")
            except sr.RequestError as e:
                print(f"❌ Error with speech recognition: {e}")
                self.gui.update_status("Speech recognition error")
        else:
            self.is_recording = False

    def speak(self, text):
        """Convert text to speech using macOS say command"""
        print(f"🤖 Agent: {text}")
        
        if self.use_macos_say:
            try:
                clean_text = re.sub(r'[^\w\s.,!?-]', '', text)
                chunks = [clean_text[i:i+200] for i in range(0, len(clean_text), 200)]
                for chunk in chunks:
                    if chunk.strip():
                        subprocess.run(['say', '-r', '200', chunk], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error with macOS say command: {e}")

    def calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        print("🎤 Calibrating microphone...")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.8
                self.recognizer.phrase_threshold = 0.3
            print("✅ Microphone calibrated successfully!")
        except Exception as e:
            print(f"⚠️ Microphone calibration warning: {e}")

    def setup_webdriver(self):
        """Setup and configure web driver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Try to find ChromeDriver
            chromedriver_paths = [
                "./chromedriver", "/usr/local/bin/chromedriver", 
                "/opt/homebrew/bin/chromedriver", "/usr/bin/chromedriver"
            ]
            
            chromedriver_path = None
            for path in chromedriver_paths:
                if os.path.exists(path):
                    chromedriver_path = path
                    break
            
            if chromedriver_path:
                service = Service(executable_path=chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ Web driver setup successful!")
            return True
        except Exception as e:
            logger.error(f"❌ Error setting up webdriver: {e}")
            return False

    def navigate_to_page(self, page_key):
        """Navigate to a specific page"""
        try:
            page_mappings = {
                'home': '/', 'about': '/about', 'services': '/services', 
                'career': '/career', 'careers': '/career', 'contact': '/contact',
                'portfolio': '/portfolio', 'blog': '/blog', 'team': '/team'
            }
            
            if page_key in page_mappings:
                url = self.website_url.rstrip('/') + page_mappings[page_key]
                print(f"🌐 Navigating to: {url}")
                self.driver.get(url)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(2)
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error navigating to {page_key}: {e}")
            return False

    def process_command(self, command):
        """Process voice commands using enhanced AI"""
        if not command:
            return True
            
        # Check for exit commands
        if any(keyword in command for keyword in ['stop', 'exit', 'quit', 'goodbye', 'bye']):
            self.speak("Thank you for using the I Knowledge Factory voice assistant. Goodbye!")
            return False
        
        # Extract detailed page content
        detailed_content = self.extract_detailed_page_content()
        
        # Get AI response with enhanced context
        ai_response = self.get_ai_response(command, detailed_content)
        
        # Extract and perform actions
        actions = self.extract_actions_from_response(ai_response, command)
        
        # Perform actions
        for action_type, action_value in actions:
            if action_type == "navigate":
                success = self.navigate_to_page(action_value)
                if success:
                    time.sleep(1)  # Allow page to load
                    detailed_content = self.extract_detailed_page_content()
            elif action_type == "apply_for_job":
                success = self.apply_for_job(action_value)
                if success:
                    ai_response += f" I've found the {action_value} position and opened the application process for you."
            elif action_type == "show_jobs":
                # Already handled by navigation to career page
                pass
        
        # Speak the AI response
        self.speak(ai_response)
        return True

    def run(self):
        """Main execution loop"""
        print("\n" + "="*60)
        print("   🤖 ENHANCED AI VOICE WEB AGENT   ")
        print("="*60)
        
        # Test API connection
        if not self.test_groq_connection():
            print("❌ Cannot proceed without working API connection.")
            return
        
        # Setup webdriver
        if not self.setup_webdriver():
            return
        
        try:
            # Open website
            print(f"🌐 Opening website: {self.website_url}")
            self.driver.get(self.website_url)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Initial page analysis
            self.extract_detailed_page_content()
            
            # Welcome message
            welcome_response = self.get_ai_response("Introduce yourself as the enhanced voice assistant for I Knowledge Factory website. Mention the push-to-talk feature and what you can help with.")
            self.speak(welcome_response)
            
            print("\n" + "="*60)
            print("🎤 PUSH-TO-TALK VOICE CONTROL READY!")
            print("- Hold the button or SPACE key to talk")
            print("- Ask about jobs, services, navigate pages")
            print("- Say 'apply for [job]' to start application process")
            print("="*60 + "\n")
            
            # Start GUI - this will block until GUI is closed
            self.gui.run()
            
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
        finally:
            if self.driver:
                self.driver.quit()
            print("✅ Enhanced AI Voice Web Agent terminated.")

if __name__ == "__main__":
    
    try:
        agent = AIVoiceWebAgent()
        agent.run()
    except KeyboardInterrupt:
        print("\n🛑 Exiting...")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🔧 Check setup requirements above")
