import contextlib
import io
import unittest
from unittest.mock import Mock, patch

from src import plc_s7_reader as reader


class S7StringTests(unittest.TestCase):
    def test_reported_buffer(self):
        data = bytearray(b'\xfe\x0521/10' + b' ' * 247)
        self.assertEqual(reader.parse_data(data, 'string', 0, 254), '21/10')

    def test_full_capacity_string(self):
        data = bytearray(b'\xfe\xfe' + b'A' * 254)
        self.assertEqual(reader.parse_data(data, 'string', 0, 254), 'A' * 254)

    def test_empty_string(self):
        self.assertEqual(reader.parse_data(bytearray(b'\x05\x00     '), 'string', 0, 5), '')

    def test_offset_encoding_and_significant_spaces(self):
        data = bytearray(b'prefix\x05\x03 \xe8 XX')
        self.assertEqual(reader.parse_data(data, 'string', 6, 5), ' è ')

    def test_invalid_or_truncated_strings(self):
        for data in (b'\x05', b'\x05\x06abcdef', b'\xff\x00', b'\x05\x05abc'):
            with self.subTest(data=data), contextlib.redirect_stdout(io.StringIO()):
                self.assertIsNone(reader.parse_data(bytearray(data), 'string', 0, 5))

    def test_cli_reads_header_and_full_capacity(self):
        plc = Mock()
        plc.read_area.return_value = bytearray(b'\xfe\xfe' + b'A' * 254)
        answers = ['1', '192.0.2.1', '', '', '', '1', '201', '686', 'string', '254', 'n']
        output = io.StringIO()
        with patch.object(reader, 'connect_to_plc', return_value=plc), \
                patch('builtins.input', side_effect=answers), contextlib.redirect_stdout(output):
            reader.main()
        plc.read_area.assert_called_once_with(reader.snap7.Area.DB, 201, 686, 256)
        self.assertIn('Parsed value: ' + 'A' * 254, output.getvalue())


class S7CharTests(unittest.TestCase):
    def test_char_bytes_preserve_spaces_nuls_and_latin1(self):
        data = bytearray(b'prefix \xe8\x00 suffix')
        self.assertEqual(reader.parse_data(data, 'char', 6, 4), ' è\x00 ')

    def test_invalid_length_or_incomplete_buffer(self):
        for index, length in ((0, None), (0, 0), (0, -1), (-1, 1), (0, 4)):
            with self.subTest(index=index, length=length), contextlib.redirect_stdout(io.StringIO()):
                self.assertIsNone(reader.parse_data(bytearray(b'abc'), 'char', index, length))

    def test_cli_reads_more_than_254_bytes_without_header(self):
        plc = Mock()
        plc.read_area.return_value = bytearray(b'A' * 300)
        answers = ['1', '192.0.2.1', '', '', '', '1', '201', '686', 'char', '300', 'n']
        output = io.StringIO()
        with patch.object(reader, 'connect_to_plc', return_value=plc), \
                patch('builtins.input', side_effect=answers), contextlib.redirect_stdout(output):
            reader.main()
        plc.read_area.assert_called_once_with(reader.snap7.Area.DB, 201, 686, 300)
        self.assertIn('Parsed value: ' + 'A' * 300, output.getvalue())

    def test_cli_rejects_invalid_count_before_reading(self):
        for count in ('0', '-1', 'abc'):
            plc = Mock()
            plc.read_area.return_value = bytearray(b'X')
            answers = ['1', '192.0.2.1', '', '', '', '1', '201', '686', 'char', count,
                       '1', '201', '686', 'char', '1', 'n']
            output = io.StringIO()
            with self.subTest(count=count), \
                    patch.object(reader, 'connect_to_plc', return_value=plc), \
                    patch('builtins.input', side_effect=answers), contextlib.redirect_stdout(output):
                reader.main()
            plc.read_area.assert_called_once_with(reader.snap7.Area.DB, 201, 686, 1)
            self.assertIn('CHAR byte count must be a positive integer.', output.getvalue())


if __name__ == '__main__':
    unittest.main()
