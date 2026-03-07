import marshal
import dis

def dump_functions(filepath):
    print(f"Functions in {filepath}:")
    with open(filepath, 'rb') as f:
        f.read(16)
        try:
            code = marshal.load(f)
            for const in code.co_consts:
                if hasattr(const, 'co_code'):
                    print(f"  def {const.co_name}")
        except Exception as e:
            print("Error:", e)

paths = [
    "/Users/princegupta09372gmail.com/Downloads/JARVIS-master-main/jarvis-system/backend/adaptive_learning/api/__pycache__/viva_controller.cpython-314.pyc",
    "/Users/princegupta09372gmail.com/Downloads/JARVIS-master-main/jarvis-system/backend/adaptive_learning/flashcards/__pycache__/generator.cpython-314.pyc",
    "/Users/princegupta09372gmail.com/Downloads/JARVIS-master-main/jarvis-system/backend/adaptive_learning/flashcards/__pycache__/spaced_repetition.cpython-314.pyc",
    "/Users/princegupta09372gmail.com/Downloads/JARVIS-master-main/jarvis-system/backend/adaptive_learning/viva_engine/__pycache__/viva_session.cpython-314.pyc",
    "/Users/princegupta09372gmail.com/Downloads/JARVIS-master-main/jarvis-system/backend/adaptive_learning/viva_engine/__pycache__/adaptive_questioner.cpython-314.pyc"
]

for p in paths:
    dump_functions(p)
