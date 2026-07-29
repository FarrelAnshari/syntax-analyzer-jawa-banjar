SYNTAX ANALYZER GRAMMAR BAHASA JAWA DAN BAHASA BANJAR
======================================================

Nama     : Farrel Maulana Anshari
NIM      : 202410370110287
Proyek   : Rekonstruksi tugas Teori Bahasa dan Otomata

1. Persyaratan
--------------
- Python 3.10 atau lebih baru disarankan.
- Tkinter. Pada instalasi Python Windows dari python.org, Tkinter biasanya sudah tersedia.
- Tidak memerlukan instalasi package tambahan.

2. Cara Menjalankan
-------------------
Buka Command Prompt/PowerShell pada folder program, lalu jalankan:

    python syntax_analyzer_jawa_banjar.py

Pada beberapa komputer, perintahnya mungkin:

    py syntax_analyzer_jawa_banjar.py

3. Cara Menggunakan
-------------------
- Pilih Bahasa Jawa atau Bahasa Banjar.
- Masukkan kalimat.
- Tekan tombol "Periksa Grammar".
- Program menampilkan status valid/tidak valid, struktur kalimat, parse tree, dan log state.

Contoh Bahasa Jawa yang valid:
    kowe mangan sego sore
    aku mangan ning omah
    kowe mangan

Contoh Bahasa Banjar yang valid:
    kita mambaca buku di rumah
    ulun makan nasi wahini
    ikam guring

Contoh tidak valid:
    mangan ning pasar sampeyan

4. Aturan Grammar
-----------------
    S -> SUBJEK PREDIKAT [OBJEK] [KETERANGAN]

Objek dan keterangan bersifat opsional. Subjek dan predikat wajib ada.

5. Pengujian Otomatis
---------------------
Jalankan:

    python syntax_analyzer_jawa_banjar.py --self-test

Program akan menguji beberapa contoh kalimat valid dan tidak valid.

6. Catatan
----------
Kosakata dapat ditambah melalui variabel GRAMMAR_DATABASE pada bagian awal file program.
