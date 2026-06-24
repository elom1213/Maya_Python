class TemplateEngine:

    @staticmethod
    def apply(text, replacements):

        for key, value in replacements.items():

            text = text.replace(
                "{{" + key + "}}",
                str(value)
            )

        return text
    
    
