from markdown_pdf import MarkdownPdf, Section

pdf = MarkdownPdf(toc_level=0)
with open("pipeline_overview.md", "r", encoding="utf-8") as f:
    text = f.read()

pdf.add_section(Section(text))
pdf.save("pipeline_overview.pdf")
print("PDF generated successfully.")
