import os
import subprocess
import sys

def main():
    # Resolve full path to the app.py inside the bundled package
    app_path = os.path.join(os.path.dirname(sys.executable), 'app.py')
    
    # Call streamlit using 'python -m streamlit run' so it works inside PyInstaller
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])

if __name__ == '__main__':
    main()

