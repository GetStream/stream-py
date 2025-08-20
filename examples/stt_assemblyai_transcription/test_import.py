#!/usr/bin/env python3
"""
Simple test script to verify the AssemblyAI STT example can be imported.
This helps catch any import or dependency issues early.
"""

def test_imports():
    """Test that all required modules can be imported."""
    try:
        # Test basic imports
        import asyncio
        print("✅ asyncio imported successfully")
        
        import logging
        print("✅ logging imported successfully")
        
        import os
        print("✅ os imported successfully")
        
        import time
        print("✅ time imported successfully")
        
        import uuid
        print("✅ uuid imported successfully")
        
        import webbrowser
        print("✅ webbrowser imported successfully")
        
        from urllib.parse import urlencode
        print("✅ urllib.parse imported successfully")
        
        # Test dotenv
        from dotenv import load_dotenv
        print("✅ python-dotenv imported successfully")
        
        # Test GetStream imports
        from getstream.models import UserRequest
        print("✅ getstream.models imported successfully")
        
        from getstream.stream import Stream
        print("✅ getstream.stream imported successfully")
        
        from getstream.video import rtc
        print("✅ getstream.video.rtc imported successfully")
        
        from getstream.video.rtc.track_util import PcmData
        print("✅ getstream.video.rtc.track_util imported successfully")
        
        # Test AssemblyAI plugin import
        from getstream.plugins.assemblyai.stt import AssemblyAISTT
        print("✅ getstream.plugins.assemblyai.stt imported successfully")
        
        print("\n🎉 All imports successful! The example should work correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please check that all dependencies are installed:")
        print("  uv sync")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_assemblyai_stt_creation():
    """Test that AssemblyAI STT can be instantiated (without API key)."""
    try:
        from getstream.plugins.assemblyai.stt import AssemblyAISTT
        
        # Try to create instance (will warn about missing API key but shouldn't crash)
        stt = AssemblyAISTT()
        print("✅ AssemblyAI STT instance created successfully")
        
        # Check basic attributes
        assert hasattr(stt, 'sample_rate')
        assert hasattr(stt, 'language')
        assert hasattr(stt, 'interim_results')
        print("✅ AssemblyAI STT has expected attributes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating AssemblyAI STT instance: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing AssemblyAI STT Example Imports")
    print("=" * 45)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    print()
    
    # Test STT creation
    if not test_assemblyai_stt_creation():
        success = False
    
    print()
    
    if success:
        print("🎯 All tests passed! The example is ready to run.")
        print("\nNext steps:")
        print("1. Copy env.example to .env")
        print("2. Add your Stream and AssemblyAI API keys")
        print("3. Run: uv run main.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        exit(1)
