import * as pdfjs from "pdfjs-dist";
import pdfWorker from "pdfjs-dist/build/pdf.worker.min.mjs?url";

pdfjs.GlobalWorkerOptions.workerSrc = pdfWorker;

const MAX_FILE_BYTES = 10 * 1024 * 1024;
const MAX_PDF_PAGES = 25;
const MAX_IMAGE_PIXELS = 24_000_000;

export async function readReceipt(file: File, onProgress: (value: number) => void): Promise<string> {
  if (!file.size || file.size > MAX_FILE_BYTES) throw new Error("El comprobante debe pesar menos de 10 MB.");
  if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
    const pdf = await pdfjs.getDocument({ data: await file.arrayBuffer() }).promise;
    if (pdf.numPages < 1 || pdf.numPages > MAX_PDF_PAGES) throw new Error("El PDF supera el límite de 25 páginas.");
    const pages: string[] = [];
    for (let number = 1; number <= Math.min(pdf.numPages, 3); number += 1) {
      const page = await pdf.getPage(number);
      const content = await page.getTextContent();
      const textItems = content.items.flatMap(item => "str" in item && item.str.trim() ? [{ str: item.str, transform: item.transform }] : []);
      const totalLabel = textItems.find(item => /^total\s*\(.*cop.*\)\s*:?$/i.test(item.str.trim()));
      let totalHint = "";
      if (totalLabel) {
        const vertical = Math.abs(totalLabel.transform[1]) > Math.abs(totalLabel.transform[0]);
        const aligned = textItems.filter(item => {
          if (!/^\s*\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{2})?\s*$/.test(item.str)) return false;
          const distance = vertical ? Math.abs(item.transform[4] - totalLabel.transform[4]) : Math.abs(item.transform[5] - totalLabel.transform[5]);
          return distance <= 3;
        }).sort((left, right) => {
          const leftDistance = vertical ? Math.abs(left.transform[5] - totalLabel.transform[5]) : Math.abs(left.transform[4] - totalLabel.transform[4]);
          const rightDistance = vertical ? Math.abs(right.transform[5] - totalLabel.transform[5]) : Math.abs(right.transform[4] - totalLabel.transform[4]);
          return leftDistance - rightDistance;
        });
        if (aligned[0]) totalHint = `TOTAL (COP): ${aligned[0].str}\n`;
      }
      pages.push(totalHint + textItems.map(item => item.str).join("\n"));
      onProgress(Math.round((number / Math.min(pdf.numPages, 3)) * 75));
    }
    const embeddedText = pages.join("\n").trim();
    if (embeddedText.length >= 30) { onProgress(100); return embeddedText; }
    const firstPage = await pdf.getPage(1);
    const viewport = firstPage.getViewport({ scale: 2 });
    const canvas = document.createElement("canvas");
    canvas.width = viewport.width; canvas.height = viewport.height;
    const context = canvas.getContext("2d");
    if (!context) throw new Error("No se pudo preparar el PDF para lectura.");
    await firstPage.render({ canvasContext: context, viewport }).promise;
    const image = await new Promise<Blob>((resolve, reject) => canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error("No se pudo convertir el PDF.")), "image/png"));
    return recognizeImage(image, onProgress);
  }
  if (!file.type.startsWith("image/")) throw new Error("Selecciona una imagen o un archivo PDF.");
  return recognizeImage(file, onProgress);
}

async function recognizeImage(image: Blob, onProgress: (value: number) => void): Promise<string> {
  const bitmap = await createImageBitmap(image);
  try {
    if (bitmap.width * bitmap.height > MAX_IMAGE_PIXELS) throw new Error("La imagen supera el límite seguro de resolución.");
  } finally { bitmap.close(); }
  const { createWorker } = await import("tesseract.js");
  const worker = await createWorker("spa", undefined, {
    langPath: `${window.location.origin}/tessdata`,
    logger: message => {
    if (message.status === "recognizing text") onProgress(Math.round((message.progress || 0) * 100));
  }});
  try {
    const text = (await worker.recognize(image)).data.text.trim();
    if (text.length < 8) throw new Error("La imagen no contiene texto legible. Acércate, evita reflejos y vuelve a intentarlo.");
    return text;
  }
  finally { await worker.terminate(); }
}
