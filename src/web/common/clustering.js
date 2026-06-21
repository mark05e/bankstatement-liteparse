/** Spatial clustering helpers for liteparse text items. */

export const DEFAULT_ROW_CLUSTER_TOLERANCE = 6.0;

export function parseAmount(text) {
  return parseFloat(text.replace("$", "").replace(/,/g, ""));
}

/** @param {Array<[string, number, number]>} columnBands */
export function columnForX(x, columnBands) {
  for (const [name, low, high] of columnBands) {
    if (x >= low && x < high) return name;
  }
  return null;
}

/** Mutates items array order (y-sort). */
export function clusterRows(items, tolerance = DEFAULT_ROW_CLUSTER_TOLERANCE) {
  items.sort((a, b) => a.y - b.y);
  const clusters = [];
  for (const item of items) {
    let matched = false;
    for (const cluster of clusters) {
      if (Math.abs(item.y - cluster.y_ref) <= tolerance) {
        cluster.items.push(item);
        matched = true;
        break;
      }
    }
    if (!matched) {
      clusters.push({ y_ref: item.y, items: [item] });
    }
  }
  return clusters;
}

export function rowFields(cluster, columnBands, mergeColumn = "description") {
  const fields = Object.fromEntries(columnBands.map(([name]) => [name, null]));
  const merged = [];
  cluster.items.sort((a, b) => a.x - b.x);
  for (const item of cluster.items) {
    const column = columnForX(item.x, columnBands);
    const text = item.text.trim();
    if (!text || column === null) continue;
    if (column === mergeColumn) {
      merged.push(text);
    } else {
      fields[column] = text;
    }
  }
  if (merged.length) {
    fields[mergeColumn] = merged.join(" ");
  }
  return fields;
}
