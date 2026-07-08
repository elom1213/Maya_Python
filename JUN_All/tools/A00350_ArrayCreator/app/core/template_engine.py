# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# A00350_ArrayCreator - {{KEY}} 치환 엔진 (A00080_KWI_creator / A00260_ConstraintConverter 와 동일 패턴)


class TemplateEngine:

    @staticmethod
    def apply(text, replacements):

        for key, value in replacements.items():

            text = text.replace(
                "{{" + key + "}}",
                str(value)
            )

        return text
