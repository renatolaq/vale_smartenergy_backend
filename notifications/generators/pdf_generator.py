from django.template.loader import get_template
import pdfkit

from SmartEnergy.settings import BASE_DIR


def generate_pdf(data, display_title, language="pt_BR"):
    template = get_template("notification_list_template.html")
    image_file = f"{BASE_DIR}/SmartEnergy/static/vale-logo.png"

    rendered_template = template.render(
        context={
            "data": data,
            "image_file": image_file,
            "display_title": display_title,
            "language_acronym": language,
        },
    )

    result = pdfkit.PDFKit(rendered_template, "string").to_pdf()
    return result
