import * as pdfjs from "pdfjs-dist";
import pdfWorker from "pdfjs-dist/build/pdf.worker.min.mjs?url";

pdfjs.GlobalWorkerOptions.workerSrc = pdfWorker;

export async function readReceipt(file: File, onProgress: (value: number) => void): Promise<string> {
  if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
    const pdf = await pdfjs.getDocument({ data: await file.arrayBuffer() }).promise;
    const pages: string[] = [];
    for (let number = 1; number <= Math.min(pdf.numPages, 3); number += 1) {
      const page = await pdf.getPage(number);
      const content = await page.getTextContent();
      pages.push(content.items.map(item => "str" in item ? item.str : "").join(" "));
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
  const { createWorker } = await import("tesseract.js");
  const worker = await createWorker("spa", undefined, { logger: message => {
    if (message.status === "recognizing text") onProgress(Math.round((message.progress || 0) * 100));
  }});
  try { return (await worker.recognize(image)).data.text; }
  finally { await worker.terminate(); }
}
