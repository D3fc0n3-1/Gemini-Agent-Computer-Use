import os
import json
import pyautogui
import time
from PIL import Image
from google import genai
from google.genai import types

# SAFETY FIRST: Move mouse to any corner to abort
pyautogui.FAILSAFE = True

class GeminiAgent:
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_API_KEY')
        self.client = genai.Client(api_key=self.api_key, http_options={'api_version': 'v1beta'})
        self.model_id = "models/gemini-3-flash-preview"

    def execute_action(self, action_json):
        try:
            data = json.loads(action_json)
            action = data.get("action")
            
            if action == "click":
                x, y = data.get("x"), data.get("y")
                print(f"[+] Clicking at: {x}, {y}")
                pyautogui.click(x, y)
            
            elif action == "type":
                text = data.get("text")
                print(f"[+] Typing: {text}")
                pyautogui.write(text, interval=0.05)
                
            elif action == "press":
                key = data.get("key")
                print(f"[+] Pressing key: {key}")
                pyautogui.press(key)
                
            time.sleep(1) # Wait for UI to react
        except Exception as e:
            print(f"[!] Failed to execute action: {e}")

    def run_agent_loop(self, goal):
        print(f"[*] Goal: {goal}")
        
        while True:
            # 1. Capture current state
            screenshot_path = "current_state.png"
            pyautogui.screenshot(screenshot_path)
            
            # 2. Ask Gemini for the next step
            with open(screenshot_path, "rb") as f:
                img_bytes = f.read()

            prompt = (
                f"You are a Windows automation agent. Goal: {goal}. "
                "Look at the screenshot and return ONLY a JSON object for the next step. "
                "Example: {\"action\": \"click\", \"x\": 500, \"y\": 300} "
                "If the task is finished, return {\"action\": \"done\"}."
            )

            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=[
                        types.Part.from_text(text=prompt),
                        types.Part.from_bytes(data=img_bytes, mime_type="image/png")
                    ]
                )
                
                res_text = response.text.strip()
                # Clean up markdown code blocks if Gemini includes them
                if "```json" in res_text:
                    res_text = res_text.split("```json")[1].split("```")[0].strip()

                if '"action": "done"' in res_text:
                    print("[*] Task complete!")
                    break

                # 3. Human-in-the-loop validation
                print(f"\n[PROPOSED ACTION]: {res_text}")
                confirm = input("Execute this action? (y/n/q): ").lower()
                
                if confirm == 'y':
                    self.execute_action(res_text)
                elif confirm == 'q':
                    break
                    
            except Exception as e:
                print(f"[!] API Error: {e}")
                break

if __name__ == "__main__":
    agent = GeminiAgent()
    # Example: Ask it to check your solar charge controller status if you have a dashboard open
    agent.run_agent_loop("Open PowerShell and check the current directory.")