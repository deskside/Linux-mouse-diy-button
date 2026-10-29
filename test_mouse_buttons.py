import unittest
from mouse_buttons import mapping, translate, identity, matches
from types import SimpleNamespace


class RemapTests(unittest.TestCase):
    def test_default_and_swapped(self):
        for code in (276, 277):
            self.assertEqual(mapping()[str(code)], 'copy')
            self.assertEqual(mapping(True)[str(code)], 'paste')
        for code in (275, 278):
            self.assertEqual(mapping()[str(code)], 'paste')

    def test_chord_is_balanced_and_original_suppressed(self):
        for code, key in ((276, 46), (275, 47)):
            self.assertEqual(translate(1, code, 1, mapping()),
                             [(1, 29, 1), (1, key, 1), (0, 0, 0),
                              (1, key, 0), (1, 29, 0), (0, 0, 0)])
            self.assertEqual(translate(1, code, 0, mapping()), [])
            self.assertEqual(translate(1, code, 2, mapping()), [])

    def test_pointer_and_other_buttons_pass_through(self):
        for event in ((2, 0, 10), (2, 8, -1), (1, 272, 1), (0, 0, 0)):
            self.assertEqual(translate(*event, mapping()), [event])

    def test_learned_nonstandard_code(self):
        self.assertEqual(translate(1, 280, 1, {'280': 'paste'})[1], (1, 47, 1))
        self.assertEqual(translate(1, 276, 1, {'280': 'paste'}), [(1, 276, 1)])

    def test_identity_includes_usb_location(self):
        dev = SimpleNamespace(name='USB Mouse', info=SimpleNamespace(vendor=1, product=2),
                              phys='usb-1/input0', uniq='')
        saved = identity(dev)
        self.assertTrue(matches(dev, saved))
        dev.phys = 'usb-2/input0'
        self.assertFalse(matches(dev, saved))


if __name__ == '__main__':
    unittest.main()
