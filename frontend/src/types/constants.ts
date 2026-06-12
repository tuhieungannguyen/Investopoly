export const TILE_MAP = [
  "GO",
  "Real Estate 1",
  "Stock Corp A",
  "Chance",
  "Real Estate 2",
  "Jail Visit",
  "Stock Corp B",
  "Shock event",
  "Savings",
  "Real Estate 3",
  "Quizzes (Education)",
  "Real Estate 4",
  "Stock Corp C",
  "Chance",
  "Stock Corp D",
  "Jail (Challenge)",
  "Stock Corp E",
  "Shock event",
  "Tax Checkpoint",
  "Real Estate 5"
] as const;

export const STOCK_TILE_NAMES = new Set([
  "Stock Corp A",
  "Stock Corp B",
  "Stock Corp C",
  "Stock Corp D",
  "Stock Corp E"
]);

export const ESTATE_TILE_NAMES = new Set([
  "Real Estate 1",
  "Real Estate 2",
  "Real Estate 3",
  "Real Estate 4",
  "Real Estate 5"
]);
