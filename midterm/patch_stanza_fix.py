import json

with open('main.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

replacements = {

  # ── Load cell: Stanza (POS only) + spaCy (NER only) ─────────────────────────
  'tfidf-pos-load-cell': [
    "import stanza\n",
    "import spacy\n",
    "\n",
    "# ── Stanza: POS tagging (Indonesian supports tokenize, mwt, pos, lemma)\n",
    "# Download once if needed: stanza.download('id')\n",
    "nlp_stanza = stanza.Pipeline(\n",
    "    lang='id',\n",
    "    processors='tokenize,mwt,pos',   # NER not available for 'id'\n",
    "    verbose=False\n",
    ")\n",
    "print('Stanza pipeline loaded (id): tokenize, mwt, pos')\n",
    "\n",
    "# ── spaCy: NER (multilingual model supports Indonesian NER)\n",
    "# Download once if needed: python -m spacy download xx_ent_wiki_sm\n",
    "try:\n",
    "    nlp_spacy = spacy.load('xx_ent_wiki_sm')\n",
    "    print('spaCy pipeline loaded: xx_ent_wiki_sm')\n",
    "except OSError:\n",
    "    raise OSError(\n",
    "        'spaCy model not found. Run:\\n'\n",
    "        '  python -m spacy download xx_ent_wiki_sm'\n",
    "    )"
  ],

  # ── POS markdown: reflect split approach ─────────────────────────────────────
  'tfidf-pos-md': [
    "---\n",
    "### 4. TF-IDF + POS Analysis\n",
    "\n",
    "POS tagging menggunakan **Stanza** (model Bahasa Indonesia `id`).\n",
    "Token difilter berdasarkan kategori:\n",
    "- **NOUN / PROPN** (kata benda & nama diri)\n",
    "- **VERB** (kata kerja)\n",
    "- **ADJ** (kata sifat)\n",
    "\n",
    "> Catatan: Stanza `id` **tidak mendukung NER** — NER ditangani spaCy (lihat Section 5).\n",
    "\n",
    "> Install jika belum:\n",
    "> ```\n",
    "> pip install stanza spacy\n",
    "> python -c \"import stanza; stanza.download('id')\"\n",
    "> python -m spacy download xx_ent_wiki_sm\n",
    "> ```"
  ],

  # ── NER markdown: mention spaCy ──────────────────────────────────────────────
  'tfidf-ner-md': [
    "---\n",
    "### 5. TF-IDF + NER Analysis\n",
    "\n",
    "NER menggunakan **spaCy** (`xx_ent_wiki_sm` — model multibahasa yang mendukung Indonesian).\n",
    "TF-IDF dijalankan per tipe entitas:\n",
    "- **PER** — nama orang\n",
    "- **ORG** — organisasi / lembaga\n",
    "- **LOC / GPE** — lokasi / tempat"
  ],

  # ── NER extraction: use nlp_spacy instead of nlp_stanza ──────────────────────
  'tfidf-ner-extract-cell': [
    "def extract_ner_tokens(text: str, ent_types: list) -> str:\n",
    "    \"\"\"Extract named entity text using spaCy (xx_ent_wiki_sm).\"\"\"\n",
    "    if not isinstance(text, str) or not text.strip():\n",
    "        return ''\n",
    "    doc = nlp_spacy(text[:5000])\n",
    "    tokens = [\n",
    "        ent.text.lower().replace(' ', '_')\n",
    "        for ent in doc.ents\n",
    "        if ent.label_ in ent_types\n",
    "        and len(ent.text.strip()) > 2\n",
    "    ]\n",
    "    return ' '.join(tokens)\n",
    "\n",
    "\n",
    "print('Extracting NER tokens (spaCy xx_ent_wiki_sm)...')\n",
    "df['ner_per'] = df['konten'].apply(lambda t: extract_ner_tokens(t, ['PER']))\n",
    "df['ner_org'] = df['konten'].apply(lambda t: extract_ner_tokens(t, ['ORG']))\n",
    "df['ner_loc'] = df['konten'].apply(lambda t: extract_ner_tokens(t, ['LOC', 'GPE']))\n",
    "print('Done!')\n",
    "\n",
    "print(f'\\nDocs with PER entities : {(df[\"ner_per\"] != \"\").sum()}')\n",
    "print(f'Docs with ORG entities : {(df[\"ner_org\"] != \"\").sum()}')\n",
    "print(f'Docs with LOC entities : {(df[\"ner_loc\"] != \"\").sum()}')\n",
    "\n",
    "print('\\nSample PER:', df['ner_per'].iloc[1].split()[:10])\n",
    "print('Sample ORG:', df['ner_org'].iloc[1].split()[:10])"
  ],
}

changed = 0
for cell in nb['cells']:
    cid = cell.get('id', '')
    if cid in replacements:
        cell['source'] = replacements[cid]
        if cell.get('cell_type') == 'code':
            cell['outputs'] = []
            cell['execution_count'] = None
        changed += 1
        print(f'  Patched: {cid}')

with open('main.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f'\nDone! {changed} cells patched.')
