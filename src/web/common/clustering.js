/** Spatial clustering helpers for liteparse text items. */

export const DEFAULT_ROW_CLUSTER_TOLERANCE = 6.0;

export function parseAmount(text) {
  return parseFloat(text.replace("$", "").replace(/,/g, ""));
}

export function columnForX(x, columns) {
  for (const [name, [low, high]] of Object.entries(columns)) {
    if (x >= low && x < high) return name;
  }
  return null;
}

export function clusterRows(items, tolerance = DEFAULT_ROW_CLUSTER_TOLERANCE) {
  const sortedItems = [...items].sort((a, b) => a.y - b.y);
  const clusters = [];
  for (const item of sortedItems) {
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

export function rowFields(cluster, columns, mergeColumn = "description") {
  const fields = Object.fromEntries(Object.keys(columns).map((name) => [name, null]));
  const merged = [];
  for (const item of [...cluster.items].sort((a, b) => a.x - b.x)) {
    const column = columnForX(item.x, columns);
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
