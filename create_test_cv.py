"""Script one-shot pour generer un cv.pdf de test minimal."""
import struct, zlib, pathlib

def make_minimal_pdf(path: str, nom: str = "Candidat Test") -> None:
    # PDF minimal valide sans dependance externe
    content = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>/Contents 4 0 R>>endobj
4 0 obj<</Length 200>>
stream
BT
/F1 18 Tf
50 780 Td
({nom}) Tj
/F1 12 Tf
0 -30 Td
(Curriculum Vitae - Document de test) Tj
0 -20 Td
(Email : votre@gmail.com) Tj
0 -20 Td
(Telephone : +226 70 00 00 00) Tj
0 -20 Td
(Ouagadougou, Burkina Faso) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
trailer<</Size 5/Root 1 0 R>>
startxref
525
%%EOF"""
    pathlib.Path(path).write_bytes(content.encode("latin-1"))
    print(f"CV de test cree : {path}")

if __name__ == "__main__":
    make_minimal_pdf("cv.pdf", "Rodrigue Tiendrebeogo")
