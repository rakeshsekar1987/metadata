#!/usr/bin/env python3
"""
Simple startup script for Home Loan EMI Calculator
Run this script to start the web application
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    requirements = [
        'flask',
        'flask-cors', 
        'reportlab',
        'matplotlib',
        'python-dateutil'
    ]
    
    for pkg in requirements:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            print(f"   Installing {pkg}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg, '-q'])
    
    print("✅ All dependencies installed!\n")

def main():
    print("\n" + "=" * 60)
    print("  🏠 Home Loan EMI Calculator")
    print("=" * 60 + "\n")
    
    # Install dependencies if needed
    try:
        import flask
        import reportlab
        import matplotlib
        from dateutil.relativedelta import relativedelta
    except ImportError:
        install_dependencies()
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run the app
    print("🚀 Starting server...\n")
    print("=" * 60)
    print("  Open your browser and go to:")
    print("  👉 http://localhost:4999")
    print("=" * 60)
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        # Import and run app
        from app import app
        app.run(host='127.0.0.1', port=4999, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTry running: python3 app.py")

if __name__ == '__main__':
    main()
