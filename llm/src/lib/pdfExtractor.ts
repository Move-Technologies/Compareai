import { PDFDocument } from "pdf-lib";

export async function extractTextFromPDF(file: File): Promise<string> {
  const arrayBuffer = await file.arrayBuffer();
  const pdfDoc = await PDFDocument.load(arrayBuffer);

  const text = await Promise.all(
    Array.from({ length: pdfDoc.getPageCount() }, async (_, i) => {
      const page = pdfDoc.getPage(i);
      return page.getText();
    })
  );

  return text.join("\n");
}
