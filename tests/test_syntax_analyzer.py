from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import syntax_analyzer_jawa_banjar as sa  # noqa: E402


class TestNormalizationAndTokenization(unittest.TestCase):
    def test_normalize_text_strips_punctuation_and_folds_case(self) -> None:
        self.assertEqual(
            sa.normalize_text("  Kowe, Mangan!  SegO?? "),
            "kowe mangan sego",
        )

    def test_tokenize_input_splits_words_and_preserves_normalized(self) -> None:
        words, normalized = sa.tokenize_input("Aku mangan ning omah.")
        self.assertEqual(words, ["aku", "mangan", "ning", "omah"])
        self.assertEqual(normalized, "aku mangan ning omah")

    def test_tokenize_empty_or_symbols_returns_empty_list(self) -> None:
        words, normalized = sa.tokenize_input("   ...!!!   ")
        self.assertEqual(words, [])
        self.assertEqual(normalized, "")


class TestLexiconClassification(unittest.TestCase):
    def test_jawa_compound_keterangan_phrase(self) -> None:
        tokens = sa.classify_tokens(["aku", "mangan", "ning", "omah"], "jawa")
        self.assertEqual(
            [(t.text, t.token_type) for t in tokens],
            [
                ("aku", sa.TokenType.SUBJEK),
                ("mangan", sa.TokenType.PREDIKAT),
                ("ning omah", sa.TokenType.KETERANGAN),
            ],
        )

    def test_banjar_compound_keterangan_phrase(self) -> None:
        tokens = sa.classify_tokens(
            ["kita", "mambaca", "buku", "di", "rumah"], "banjar"
        )
        self.assertEqual(
            [(t.text, t.token_type) for t in tokens],
            [
                ("kita", sa.TokenType.SUBJEK),
                ("mambaca", sa.TokenType.PREDIKAT),
                ("buku", sa.TokenType.OBJEK),
                ("di rumah", sa.TokenType.KETERANGAN),
            ],
        )

    def test_unknown_word_is_tagged_unknown(self) -> None:
        tokens = sa.classify_tokens(["aku", "komputer"], "jawa")
        self.assertEqual(tokens[1].token_type, sa.TokenType.UNKNOWN)


class TestCFGParserJawa(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = sa.CFGParser("jawa")

    def test_valid_sentences_jawa(self) -> None:
        valid_cases = [
            "kowe mangan",
            "aku mangan sego",
            "aku mangan ning omah",
            "kowe mangan sego sore",
            "KOWE, Mangan! SegO Sore.",
        ]
        for sentence in valid_cases:
            with self.subTest(sentence=sentence):
                result = self.parser.analyze(sentence)
                self.assertTrue(result.valid, msg=result.error_message)
                self.assertIn("S (Kalimat)", result.parse_tree)

    def test_parse_tree_labels_for_full_structure(self) -> None:
        result = self.parser.analyze("kowe mangan sego sore")
        self.assertTrue(result.valid)
        self.assertEqual(
            result.structures,
            [
                ("Subjek", "kowe"),
                ("Predikat", "mangan"),
                ("Objek", "sego"),
                ("Keterangan", "sore"),
            ],
        )
        for label in ("FN (Subjek)", "FV (Predikat)", "FN (Objek)", "FP (Keterangan)"):
            self.assertIn(label, result.parse_tree)

    def test_invalid_sentences_jawa(self) -> None:
        invalid_cases = [
            ("", "Masukkan kalimat"),
            ("aku", "PREDIKAT"),
            ("mangan ning pasar sampeyan", "SUBJEK"),
            ("kowe sego", "PREDIKAT"),
            ("aku mangan ning omah sore", "setelah struktur kalimat selesai"),
            ("aku terbang", "tidak dikenali"),
        ]
        for sentence, expected_msg in invalid_cases:
            with self.subTest(sentence=sentence):
                result = self.parser.analyze(sentence)
                self.assertFalse(result.valid)
                self.assertIn(expected_msg, result.error_message)


class TestCFGParserBanjar(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = sa.CFGParser("banjar")

    def test_unsupported_language_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            sa.CFGParser("sunda")

    def test_valid_sentences_banjar(self) -> None:
        for sentence in (
            "ikam guring",
            "ulun makan nasi",
            "ulun makan nasi wahini",
            "kita mambaca buku di rumah",
        ):
            with self.subTest(sentence=sentence):
                result = self.parser.analyze(sentence)
                self.assertTrue(result.valid, msg=result.error_message)

    def test_invalid_sentences_banjar(self) -> None:
        for sentence in ("makan nasi ulun", "ulun terbang", "buku ulun"):
            with self.subTest(sentence=sentence):
                result = self.parser.analyze(sentence)
                self.assertFalse(result.valid)


class TestSelfTestEntrypoint(unittest.TestCase):
    def test_builtin_self_test_passes(self) -> None:
        self.assertEqual(sa.run_self_test(), 0)


if __name__ == "__main__":
    unittest.main()
