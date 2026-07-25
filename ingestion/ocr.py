


def ocr_extraction(image_path : str , reader = None) -> str: 
    if reader is None: 
        import easyocr
        reader = easyocr.Reader(
            ['en'] , gpu=False , verbose=False
        )

    results = reader.readtext(image_path , detail=0)

    return " ".join(results)


