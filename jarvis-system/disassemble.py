import marshal
import struct
import sys
import dis

def analyze_pyc(filepath):
    print(f"--- Analyzing {filepath} ---")
    with open(filepath, 'rb') as f:
        # PEP 552: 16 bytes header in Python 3.7+
        f.read(16)
        try:
            code = marshal.load(f)
            dis.dis(code)
            for const in code.co_consts:
                if hasattr(const, 'co_code'):
                    print(f"\n--- Function: {const.co_name} ---")
                    dis.dis(const)
        except Exception as e:
            print("Error:", e)

analyze_pyc("/Users/princegupta09372gmail.com/Downloads/JARVIS-master-main/jarvis-system/backend/adaptive_learning/api/__pycache__/flashcard_controller.cpython-314.pyc")
