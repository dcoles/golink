import unittest

from golink import model


class GolinkTestCase(unittest.TestCase):
    def assert_urljoin(self, expected: str, golink: model.Golink, path: str):
        self.assertEqual(expected, golink.with_suffix(path))

    def test_urljoin_netloc_only(self):
        golink = model.Golink('test', 'http://www.example.com')
        self.assert_urljoin('http://www.example.com', golink, '')
        self.assert_urljoin('http://www.example.com/123', golink, '123')
        self.assert_urljoin('http://www.example.com/123', golink, '/123')

    def test_urljoin_path(self):
        golink = model.Golink('test', 'http://www.example.com/path')
        self.assert_urljoin('http://www.example.com/path', golink, '')
        self.assert_urljoin('http://www.example.com/path123', golink, '123')
        self.assert_urljoin('http://www.example.com/path/123', golink, '/123')

    def test_urljoin_full_path(self):
        golink = model.Golink('test', 'http://www.example.com/path/')
        self.assert_urljoin('http://www.example.com/path/', golink, '')
        self.assert_urljoin('http://www.example.com/path/123', golink, '123')
        self.assert_urljoin('http://www.example.com/path//123', golink, '/123')

    def test_urljoin_path_with_query(self):
        golink = model.Golink('test', 'http://www.example.com/path?q=')
        self.assert_urljoin('http://www.example.com/path?q=', golink, '')
        self.assert_urljoin('http://www.example.com/path?q=123', golink, '123')
        self.assert_urljoin('http://www.example.com/path?q=/123', golink, '/123')

    def test_urljoin_with_fragments(self):
        golink = model.Golink('test', 'http://www.example.com/path#foo')
        self.assert_urljoin('http://www.example.com/path#foo', golink, '')
        self.assert_urljoin('http://www.example.com/path#foo123', golink, '123')


if __name__ == '__main__':
    unittest.main()
