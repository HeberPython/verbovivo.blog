const path = require("path");
const { chromium } = require("playwright");

async function main() {
  const root = path.resolve(__dirname);
  const htmlPath = path.join(root, "frontpage.html");
  const outPath = path.join(root, "verbovivo-frontpage.pdf");
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1240, height: 1754 } });

  await page.goto(`file://${htmlPath.replace(/\\/g, "/")}`, { waitUntil: "networkidle" });
  await page.pdf({
    path: outPath,
    format: "A4",
    printBackground: true,
    margin: { top: "0", right: "0", bottom: "0", left: "0" },
  });

  await browser.close();
  console.log(outPath);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
