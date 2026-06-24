def process_file(file_path):

    try:

        with open(file_path, "r", encoding="utf-8") as f:

            text = f.read()

        return f"Loaded {len(text)} characters"

    except Exception as e:

        return str(e)