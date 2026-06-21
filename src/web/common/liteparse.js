/** Normalize LiteParse WASM output to the snake_case page shape extractors expect. */
export function liteparseResultToPages(result) {
  return result.pages.map((p) => ({
    page: p.pageNum,
    text: p.text,
    text_items: p.textItems.map((item) => ({
      text: item.text,
      x: item.x,
      y: item.y,
    })),
  }));
}
