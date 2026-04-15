"""
Test which Gemini models are available with your API key
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ GOOGLE_API_KEY not found in .env file")
    exit(1)

print(f"\n{'='*70}")
print(f"GEMINI MODEL AVAILABILITY TEST")
print(f"{'='*70}")
print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
print(f"{'='*70}\n")

# Configure API
genai.configure(api_key=api_key)

print("🔍 Discovering available models...\n")

try:
    models = genai.list_models()
    
    gemini_models = []
    for model in models:
        name = model.name
        methods = model.supported_generation_methods
        
        if "generateContent" in methods:
            gemini_models.append({
                "name": name,
                "display_name": model.display_name,
                "description": model.description[:100] if model.description else "No description"
            })
    
    if gemini_models:
        print(f"✅ Found {len(gemini_models)} models that support generateContent:\n")
        
        for i, model in enumerate(gemini_models, 1):
            print(f"{i}. {model['name']}")
            print(f"   Display: {model['display_name']}")
            print(f"   Description: {model['description']}")
            print()
    else:
        print("❌ No models found that support generateContent")
        print("\nℹ️  This might mean:")
        print("   1. API key doesn't have access to Gemini models")
        print("   2. API key is invalid or expired")
        print("   3. Gemini API is not enabled for this project")
        
except Exception as e:
    print(f"❌ Error listing models: {e}")
    print("\nℹ️  Possible issues:")
    print("   1. Invalid API key")
    print("   2. API not enabled")
    print("   3. Network connection issue")
    exit(1)

# Test each model
print(f"\n{'='*70}")
print(f"TESTING MODELS")
print(f"{'='*70}\n")

test_prompt = "Say 'Hello, I am working!' in exactly those words."

models_to_test = [
    "gemini-1.5-flash",
    "models/gemini-1.5-flash",
    "gemini-1.5-pro",
    "models/gemini-1.5-pro",
    "gemini-pro",
    "models/gemini-pro",
]

working_models = []

for model_name in models_to_test:
    try:
        print(f"Testing: {model_name}...", end=" ")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(test_prompt)
        text = response.text.strip()
        
        if text:
            print(f"✅ WORKS")
            print(f"   Response: {text[:50]}...")
            working_models.append(model_name)
        else:
            print(f"⚠️  Empty response")
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            print(f"❌ Not found (404)")
        elif "403" in error_msg:
            print(f"❌ Access denied (403)")
        else:
            print(f"❌ Error: {error_msg[:50]}")

print(f"\n{'='*70}")
print(f"SUMMARY")
print(f"{'='*70}\n")

if working_models:
    print(f"✅ {len(working_models)} working model(s) found:\n")
    for model in working_models:
        print(f"   • {model}")
    
    print(f"\n💡 RECOMMENDATION:")
    print(f"   Use this model in your code: {working_models[0]}")
    
else:
    print("❌ No working models found!")
    print("\n🔧 SOLUTIONS:")
    print("   1. Check your API key at: https://makersuite.google.com/app/apikey")
    print("   2. Generate a new API key")
    print("   3. Enable Gemini API in Google Cloud Console")
    print("   4. Try using OpenAI instead")

print(f"\n{'='*70}\n")
