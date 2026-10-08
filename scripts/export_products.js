// Turns the website's js/products.js into data/seed_data.json
//
// Usage (from the beelinx-api folder):
//   node scripts/export_products.js path/to/beelinx.github.io/js/products.js
//
// Re-run it any time products.js changes, then run: python -m scripts.seed

const fs = require("fs");
const vm = require("vm");
const path = require("path");

const src = process.argv[2];
if (!src) {
  console.error("Usage: node scripts/export_products.js <path-to-products.js>");
  process.exit(1);
}

const out = path.join(__dirname, "..", "data", "seed_data.json");
const code = fs.readFileSync(src, "utf8");

// products.js declares top-level consts. Run it in a sandbox and
// read them back with a final expression.
const data = vm.runInNewContext(
  code + "\n;({ featuredProducts, brandAds, brands, products });"
);

fs.writeFileSync(out, JSON.stringify(data, null, 2), "utf8");

console.log(
  `Wrote ${out}\n` +
    `  brands:   ${Object.keys(data.brands).length}\n` +
    `  products: ${Object.keys(data.products).length}\n` +
    `  featured: ${data.featuredProducts.length}\n` +
    `  ads:      ${data.brandAds.length}`
);
