import requests
import json
import time

def test_ollama():
    print("Testing Ollama with llama3.1...")
    
    payload = {
        "model": "llama3.1",
        "prompt": "Hello, who are you?",
        "stream": False
    }
    
    try:
        start = time.time()
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=30)
        end = time.time()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Response time: {end - start:.2f}s")
            print(f"Response: {result['response']}")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_ollama()
