/** Helpers for multi-PDF batch processing and ZIP downloads. */

export function filterPdfFiles(fileList) {
  const all = [...fileList];
  const pdfs = all.filter((f) => f.type === "application/pdf");
  return { pdfs, skipped: all.length - pdfs.length };
}

export function resultFilename(source, ext) {
  return source.replace(/\.pdf$/i, `.${ext}`);
}

export async function buildZipBlob(entries) {
  const JSZip = (await import("https://cdn.jsdelivr.net/npm/jszip@3.10.1/+esm")).default;
  const zip = new JSZip();
  for (const { filename, content } of entries) {
    zip.file(filename, content);
  }
  return zip.generateAsync({ type: "blob" });
}
