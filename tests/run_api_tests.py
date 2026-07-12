import sys
import os

# Ensure the root of the project is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from tests.test_api import test_get_root, test_post_recommend
    print("Running test_get_root...")
    test_get_root()
    print("test_get_root: PASS")
    
    print("Running test_post_recommend...")
    test_post_recommend()
    print("test_post_recommend: PASS")
    
    print("\nAPI Test Suite Result: SUCCESS")
    sys.exit(0)
except Exception as e:
    import traceback
    print("\nAPI Test Suite Result: FAILED")
    traceback.print_exc()
    sys.exit(1)
