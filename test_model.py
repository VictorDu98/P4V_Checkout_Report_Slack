import unittest
import model
from P4 import P4, P4Exception

class TestP4(unittest.TestCase,model.Model):

    def test_login(self):
        preset = model.Model("GFH")
        preset.init_p4()
        self.assertTrue(preset.p4.run_login(), "Not connected")

if __name__ == '__main__':
    unittest.main()