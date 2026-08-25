import pymupdf

ruta_pdf = r"../MUSSE-ManualDeMarca.pdf"
ruta_imagen = r"webapp/media/img/primera_pagina.png"

pdf = pymupdf.open(ruta_pdf)

pagina = pdf[0]
pix = pagina.get_pixmap(dpi=200)

pix.save(ruta_imagen)

pdf.close()