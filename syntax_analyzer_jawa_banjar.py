"""
Syntax Analyzer Grammar Bahasa Jawa dan Bahasa Banjar
=====================================================

Rekonstruksi program tugas Teori Bahasa dan Otomata.
Program memanfaatkan:
- Regular Expression untuk normalisasi dan tokenisasi.
- Pengenalan token berbasis leksikon sebagai FSA sederhana.
- State machine untuk memvalidasi urutan CFG:
  S -> SUBJEK PREDIKAT [OBJEK] [KETERANGAN]
- Tkinter sebagai antarmuka grafis.

Program hanya menggunakan pustaka standar Python sehingga dapat dijalankan tanpa
menginstal paket tambahan.
"""

from __future__ import annotations

import argparse
import re
import tkinter as tk
from dataclasses import dataclass
from enum import Enum, auto
from tkinter import messagebox, ttk
from typing import Dict, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# DATABASE GRAMMAR / SIMBOL TERMINAL
# ---------------------------------------------------------------------------
GRAMMAR_DATABASE: Dict[str, Dict[str, object]] = {
    "jawa": {
        "name": "Bahasa Jawa",
        "subjek": [
            "aku", "kulo", "kowe", "dheweke", "awakdewe", "sampeyan",
            "bocah", "wong", "guru", "ibu", "bapak", "jeneng",
        ],
        "predikat": [
            "mangan", "turu", "mlaku", "sinau", "gawe", "maca", "nulis",
            "nonton", "main", "tuku", "nyilih", "ngombe", "lunga",
        ],
        "objek": [
            "sego", "buku", "bolpen", "sandal", "klambi", "wedang", "roti",
            "kopi", "motor", "pit", "nasi", "tv", "layang",
        ],
        "keterangan": [
            "omah", "pasar", "kampus", "sekolah", "esuk", "sore", "bengi",
            "saiki", "sesuk", "wingi", "cepet", "alon", "tenang",
        ],
        "preposisi": ["ning", "ing", "menyang", "saka", "kanthi"],
    },
    "banjar": {
        "name": "Bahasa Banjar",
        "subjek": [
            "ulun", "ikam", "sidin", "kita", "pian", "inya", "urang",
            "anak", "mama", "abah", "guru",
        ],
        "predikat": [
            "makan", "guring", "bajalan", "balajar", "bakarja", "mambaca",
            "manulis", "manonton", "bamainan", "mambali", "minum", "bulik",
        ],
        "objek": [
            "nasi", "buku", "pulpen", "sandal", "baju", "kawa", "ruti",
            "teh", "mobil", "sapeda", "tv", "tilam", "batis",
        ],
        "keterangan": [
            "rumah", "pasar", "kampus", "sakulah", "isuk", "sore", "malam",
            "wahini", "besok", "semalam", "lakasi", "capati", "lambat", "higa",
        ],
        "preposisi": ["di", "ka", "dari", "higa"],
    },
}


class TokenType(str, Enum):
    SUBJEK = "SUBJEK"
    PREDIKAT = "PREDIKAT"
    OBJEK = "OBJEK"
    KETERANGAN = "KETERANGAN"
    UNKNOWN = "UNKNOWN"


class ParserState(Enum):
    EXPECT_SUBJEK = auto()
    EXPECT_PREDIKAT = auto()
    EXPECT_OBJEK_OR_KET_OR_END = auto()
    EXPECT_KET_OR_END = auto()
    END = auto()
    REJECT = auto()


@dataclass(frozen=True)
class ClassifiedToken:
    text: str
    token_type: TokenType


@dataclass
class AnalysisResult:
    valid: bool
    language_name: str
    normalized_text: str
    tokens: List[ClassifiedToken]
    structures: List[Tuple[str, str]]
    parse_tree: str
    logs: List[str]
    error_message: str = ""


# ---------------------------------------------------------------------------
# TOKENISASI DAN IDENTIFIKASI TOKEN (REGEX / FSA)
# ---------------------------------------------------------------------------
def normalize_text(text: str) -> str:
    """Ubah input menjadi lowercase, hilangkan tanda baca, dan rapikan spasi."""
    lowered = text.lower().strip()
    # Pertahankan huruf Latin dan spasi. Karakter lain diubah menjadi spasi.
    cleaned = re.sub(r"[^a-zà-öø-ÿ\s]", " ", lowered, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


def tokenize_input(text: str) -> Tuple[List[str], str]:
    normalized = normalize_text(text)
    return (normalized.split(" ") if normalized else []), normalized


def _as_set(grammar: Dict[str, object], key: str) -> set[str]:
    return set(grammar.get(key, []))  # type: ignore[arg-type]


def classify_tokens(words: Sequence[str], language: str) -> List[ClassifiedToken]:
    """
    Klasifikasikan token dengan pencocokan leksikon.

    Frasa keterangan seperti "ning omah" atau "di rumah" digabung menjadi satu token
    KETERANGAN agar sesuai dengan aturan CFG pada laporan.
    """
    grammar = GRAMMAR_DATABASE[language]
    subjects = _as_set(grammar, "subjek")
    predicates = _as_set(grammar, "predikat")
    objects = _as_set(grammar, "objek")
    adverbs = _as_set(grammar, "keterangan")
    prepositions = _as_set(grammar, "preposisi")

    output: List[ClassifiedToken] = []
    i = 0
    while i < len(words):
        word = words[i]

        # Preposisi + kata keterangan/lokasi dianggap satu frasa keterangan.
        if word in prepositions:
            if i + 1 < len(words) and words[i + 1] in adverbs:
                output.append(
                    ClassifiedToken(f"{word} {words[i + 1]}", TokenType.KETERANGAN)
                )
                i += 2
                continue
            output.append(ClassifiedToken(word, TokenType.KETERANGAN))
            i += 1
            continue

        if word in subjects:
            token_type = TokenType.SUBJEK
        elif word in predicates:
            token_type = TokenType.PREDIKAT
        elif word in objects:
            token_type = TokenType.OBJEK
        elif word in adverbs:
            token_type = TokenType.KETERANGAN
        else:
            token_type = TokenType.UNKNOWN

        output.append(ClassifiedToken(word, token_type))
        i += 1

    return output


# ---------------------------------------------------------------------------
# CFG PARSER BERBASIS STATE MACHINE
# ---------------------------------------------------------------------------
class CFGParser:
    """Parser untuk grammar S -> SUBJEK PREDIKAT [OBJEK] [KETERANGAN]."""

    def __init__(self, language: str) -> None:
        if language not in GRAMMAR_DATABASE:
            raise ValueError(f"Bahasa tidak didukung: {language}")
        self.language = language
        self.language_name = str(GRAMMAR_DATABASE[language]["name"])

    def analyze(self, text: str) -> AnalysisResult:
        words, normalized = tokenize_input(text)
        logs: List[str] = [
            f"[START] Analisis sintaks - {self.language_name}",
            "-" * 58,
        ]

        if not words:
            return AnalysisResult(
                valid=False,
                language_name=self.language_name,
                normalized_text=normalized,
                tokens=[],
                structures=[],
                parse_tree="Parse tree tidak tersedia.",
                logs=logs + ["[REJECT] Input kalimat masih kosong."],
                error_message="Masukkan kalimat terlebih dahulu.",
            )

        tokens = classify_tokens(words, self.language)
        for index, token in enumerate(tokens):
            logs.append(
                f"[FSA] Token[{index}] '{token.text}' -> {token.token_type.value}"
            )

        logs.extend(["-" * 58, "[CFG] Memvalidasi struktur kalimat..."])

        state = ParserState.EXPECT_SUBJEK
        structures: List[Tuple[str, str]] = []

        for token in tokens:
            logs.append(
                f"[STATE] {state.name} menerima '{token.text}' "
                f"({token.token_type.value})"
            )

            if token.token_type == TokenType.UNKNOWN:
                state = ParserState.REJECT
                error = f"Kata '{token.text}' tidak dikenali dalam database grammar."
                logs.append(f"[REJECT] {error}")
                return self._build_result(
                    False, normalized, tokens, structures, logs, error
                )

            if state == ParserState.EXPECT_SUBJEK:
                if token.token_type != TokenType.SUBJEK:
                    state = ParserState.REJECT
                    error = (
                        "Kalimat harus diawali SUBJEK, bukan "
                        f"{token.token_type.value}."
                    )
                    logs.append(f"[REJECT] {error}")
                    return self._build_result(
                        False, normalized, tokens, structures, logs, error
                    )
                structures.append(("Subjek", token.text))
                state = ParserState.EXPECT_PREDIKAT

            elif state == ParserState.EXPECT_PREDIKAT:
                if token.token_type != TokenType.PREDIKAT:
                    state = ParserState.REJECT
                    error = (
                        "Setelah SUBJEK harus terdapat PREDIKAT, bukan "
                        f"{token.token_type.value}."
                    )
                    logs.append(f"[REJECT] {error}")
                    return self._build_result(
                        False, normalized, tokens, structures, logs, error
                    )
                structures.append(("Predikat", token.text))
                state = ParserState.EXPECT_OBJEK_OR_KET_OR_END

            elif state == ParserState.EXPECT_OBJEK_OR_KET_OR_END:
                if token.token_type == TokenType.OBJEK:
                    structures.append(("Objek", token.text))
                    state = ParserState.EXPECT_KET_OR_END
                elif token.token_type == TokenType.KETERANGAN:
                    structures.append(("Keterangan", token.text))
                    state = ParserState.END
                else:
                    state = ParserState.REJECT
                    error = (
                        "Setelah PREDIKAT hanya boleh OBJEK, KETERANGAN, "
                        "atau akhir kalimat."
                    )
                    logs.append(f"[REJECT] {error}")
                    return self._build_result(
                        False, normalized, tokens, structures, logs, error
                    )

            elif state == ParserState.EXPECT_KET_OR_END:
                if token.token_type == TokenType.KETERANGAN:
                    structures.append(("Keterangan", token.text))
                    state = ParserState.END
                else:
                    state = ParserState.REJECT
                    error = (
                        "Setelah OBJEK hanya boleh KETERANGAN atau akhir kalimat."
                    )
                    logs.append(f"[REJECT] {error}")
                    return self._build_result(
                        False, normalized, tokens, structures, logs, error
                    )

            elif state == ParserState.END:
                state = ParserState.REJECT
                error = "Terdapat token tambahan setelah struktur kalimat selesai."
                logs.append(f"[REJECT] {error}")
                return self._build_result(
                    False, normalized, tokens, structures, logs, error
                )

        # Evaluasi state ketika seluruh token selesai diproses.
        if state == ParserState.EXPECT_PREDIKAT:
            error = "Kalimat belum memiliki PREDIKAT."
            logs.append(f"[REJECT] {error}")
            return self._build_result(False, normalized, tokens, structures, logs, error)

        if state in {
            ParserState.EXPECT_OBJEK_OR_KET_OR_END,
            ParserState.EXPECT_KET_OR_END,
            ParserState.END,
        }:
            logs.append("[ACCEPT] Struktur kalimat sesuai aturan CFG.")
            return self._build_result(True, normalized, tokens, structures, logs, "")

        error = "Struktur kalimat tidak dapat diterima."
        logs.append(f"[REJECT] {error}")
        return self._build_result(False, normalized, tokens, structures, logs, error)

    def _build_result(
        self,
        valid: bool,
        normalized: str,
        tokens: List[ClassifiedToken],
        structures: List[Tuple[str, str]],
        logs: List[str],
        error: str,
    ) -> AnalysisResult:
        return AnalysisResult(
            valid=valid,
            language_name=self.language_name,
            normalized_text=normalized,
            tokens=tokens,
            structures=structures,
            parse_tree=build_parse_tree(structures) if valid else "Parse tree tidak tersedia untuk kalimat yang tidak valid.",
            logs=logs,
            error_message=error,
        )


def build_parse_tree(structures: Sequence[Tuple[str, str]]) -> str:
    lines = ["S (Kalimat)", "│"]
    for index, (label, word) in enumerate(structures):
        is_last = index == len(structures) - 1
        branch = "└──" if is_last else "├──"
        child_prefix = "    " if is_last else "│   "
        phrase = {
            "Subjek": "FN",
            "Predikat": "FV",
            "Objek": "FN",
            "Keterangan": "FP",
        }.get(label, "F")
        lines.append(f"{branch} {phrase} ({label})")
        lines.append(f"{child_prefix}└── '{word}'")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# GUI TKINTER
# ---------------------------------------------------------------------------
class SyntaxAnalyzerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Syntax Analyzer Grammar Bahasa Jawa dan Bahasa Banjar")
        self.root.geometry("1180x760")
        self.root.minsize(1000, 680)

        self.language_var = tk.StringVar(value="jawa")
        self.status_var = tk.StringVar(value="Silakan masukkan kalimat.")

        self._configure_style()
        self._build_ui()
        self._refresh_rules()

    def _configure_style(self) -> None:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        style.configure("Status.TLabel", font=("Segoe UI", 11, "bold"), padding=10)

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        title = ttk.Label(
            main,
            text="Syntax Analyzer Grammar Bahasa Jawa dan Bahasa Banjar",
            style="Title.TLabel",
        )
        title.pack(anchor="w", pady=(0, 10))

        paned = ttk.Panedwindow(main, orient="horizontal")
        paned.pack(fill="both", expand=True)

        left = ttk.Frame(paned, padding=(0, 0, 8, 0))
        right = ttk.Frame(paned, padding=(8, 0, 0, 0))
        paned.add(left, weight=3)
        paned.add(right, weight=2)

        # Pilihan bahasa
        lang_frame = ttk.LabelFrame(
            left, text="Pilih Bahasa", style="Section.TLabelframe"
        )
        lang_frame.pack(fill="x", pady=(0, 8))
        ttk.Radiobutton(
            lang_frame,
            text="Bahasa Jawa",
            value="jawa",
            variable=self.language_var,
            command=self._refresh_rules,
        ).pack(side="left", padx=12, pady=8)
        ttk.Radiobutton(
            lang_frame,
            text="Bahasa Banjar",
            value="banjar",
            variable=self.language_var,
            command=self._refresh_rules,
        ).pack(side="left", padx=12, pady=8)

        # Input
        input_frame = ttk.LabelFrame(
            left, text="Input Kalimat", style="Section.TLabelframe"
        )
        input_frame.pack(fill="x", pady=(0, 8))
        self.input_text = tk.Text(
            input_frame,
            height=5,
            font=("Segoe UI", 11),
            wrap="word",
            padx=8,
            pady=8,
        )
        self.input_text.pack(fill="x", padx=8, pady=8)
        self.input_text.bind("<Control-Return>", lambda _event: self.analyze())

        button_frame = ttk.Frame(left)
        button_frame.pack(fill="x", pady=(0, 8))
        ttk.Button(
            button_frame,
            text="Periksa Grammar",
            style="Primary.TButton",
            command=self.analyze,
        ).pack(side="left", fill="x", expand=True)
        ttk.Button(
            button_frame,
            text="Contoh",
            command=self.insert_example,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            button_frame,
            text="Bersihkan",
            command=self.clear_all,
        ).pack(side="left", padx=(8, 0))

        # Aturan grammar
        rules_frame = ttk.LabelFrame(
            left, text="Aturan Tata Bahasa (CFG)", style="Section.TLabelframe"
        )
        rules_frame.pack(fill="both", expand=True)
        self.rules_text = tk.Text(
            rules_frame,
            height=18,
            font=("Consolas", 9),
            wrap="word",
            state="disabled",
            padx=8,
            pady=8,
        )
        self.rules_text.pack(fill="both", expand=True, padx=8, pady=8)

        # Hasil analisis
        result_frame = ttk.LabelFrame(
            right, text="Hasil Analisis", style="Section.TLabelframe"
        )
        result_frame.pack(fill="x", pady=(0, 8))
        self.status_label = ttk.Label(
            result_frame,
            textvariable=self.status_var,
            style="Status.TLabel",
            anchor="center",
            justify="center",
        )
        self.status_label.pack(fill="x", padx=8, pady=8)
        self.structure_text = tk.Text(
            result_frame,
            height=6,
            font=("Segoe UI", 9),
            state="disabled",
            wrap="word",
            padx=8,
            pady=8,
        )
        self.structure_text.pack(fill="x", padx=8, pady=(0, 8))

        # Parse tree
        tree_frame = ttk.LabelFrame(
            right, text="Parse Tree (Pohon Parsing)", style="Section.TLabelframe"
        )
        tree_frame.pack(fill="both", expand=True, pady=(0, 8))
        self.tree_text = tk.Text(
            tree_frame,
            height=12,
            font=("Consolas", 10),
            state="disabled",
            wrap="none",
            padx=8,
            pady=8,
        )
        self.tree_text.pack(fill="both", expand=True, padx=8, pady=8)

        # Log proses
        log_frame = ttk.LabelFrame(
            right, text="Log Proses Parsing", style="Section.TLabelframe"
        )
        log_frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(
            log_frame,
            height=12,
            font=("Consolas", 8),
            state="disabled",
            bg="#151515",
            fg="#66ff66",
            insertbackground="white",
            wrap="word",
            padx=8,
            pady=8,
        )
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)

    @staticmethod
    def _replace_text(widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def _refresh_rules(self) -> None:
        language = self.language_var.get()
        grammar = GRAMMAR_DATABASE[language]
        rules = [
            "ATURAN PRODUKSI:",
            "S -> SUBJEK PREDIKAT [OBJEK] [KETERANGAN]",
            "[ ] = komponen opsional",
            "",
            f"DATABASE TOKEN - {grammar['name'].upper()}:",
            "",
            "SUBJEK:\n  " + ", ".join(grammar["subjek"]),  # type: ignore[index]
            "",
            "PREDIKAT:\n  " + ", ".join(grammar["predikat"]),  # type: ignore[index]
            "",
            "OBJEK:\n  " + ", ".join(grammar["objek"]),  # type: ignore[index]
            "",
            "KETERANGAN:\n  " + ", ".join(grammar["keterangan"]),  # type: ignore[index]
            "",
            "PREPOSISI:\n  " + ", ".join(grammar["preposisi"]),  # type: ignore[index]
        ]
        self._replace_text(self.rules_text, "\n".join(rules))

    def insert_example(self) -> None:
        example = (
            "kowe mangan sego sore"
            if self.language_var.get() == "jawa"
            else "kita mambaca buku di rumah"
        )
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", example)
        self.analyze()

    def clear_all(self) -> None:
        self.input_text.delete("1.0", "end")
        self.status_var.set("Silakan masukkan kalimat.")
        self.status_label.configure(background="")
        self._replace_text(self.structure_text, "")
        self._replace_text(self.tree_text, "")
        self._replace_text(self.log_text, "")

    def analyze(self) -> AnalysisResult:
        text = self.input_text.get("1.0", "end").strip()
        parser = CFGParser(self.language_var.get())
        result = parser.analyze(text)
        self.display_result(result)
        return result

    def display_result(self, result: AnalysisResult) -> None:
        if result.valid:
            self.status_var.set(
                f"✓ KALIMAT VALID\nStruktur tata bahasa {result.language_name} sesuai aturan CFG."
            )
            self.status_label.configure(background="#c8f7d4")
        else:
            self.status_var.set(f"✗ KALIMAT TIDAK VALID\n{result.error_message}")
            self.status_label.configure(background="#ffd6d6")

        if result.structures:
            structure_lines = ["Struktur terdeteksi:"] + [
                f"• {label}: {word}" for label, word in result.structures
            ]
        else:
            structure_lines = ["Struktur belum dapat dideteksi."]

        self._replace_text(self.structure_text, "\n".join(structure_lines))
        self._replace_text(self.tree_text, result.parse_tree)
        self._replace_text(self.log_text, "\n".join(result.logs))


def run_self_test() -> int:
    tests = [
        ("jawa", "kowe mangan sego sore", True),
        ("jawa", "aku mangan ning omah", True),
        ("jawa", "kowe mangan", True),
        ("jawa", "mangan ning pasar sampeyan", False),
        ("jawa", "kowe sego", False),
        ("banjar", "kita mambaca buku di rumah", True),
        ("banjar", "ulun makan nasi wahini", True),
        ("banjar", "ikam guring", True),
        ("banjar", "makan nasi ulun", False),
        ("banjar", "ulun terbang", False),
    ]

    failures = 0
    for language, sentence, expected in tests:
        result = CFGParser(language).analyze(sentence)
        status = "PASS" if result.valid == expected else "FAIL"
        print(f"[{status}] {language:6s} | {sentence!r} -> {result.valid}")
        if result.valid != expected:
            failures += 1
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Syntax Analyzer Jawa dan Banjar")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Jalankan pengujian parser tanpa membuka GUI.",
    )
    args = parser.parse_args()

    if args.self_test:
        raise SystemExit(run_self_test())

    root = tk.Tk()
    app = SyntaxAnalyzerApp(root)
    app.input_text.focus_set()
    root.mainloop()


if __name__ == "__main__":
    main()
