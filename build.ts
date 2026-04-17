import { watch } from "fs";
import { copyFile, mkdir } from "fs/promises";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const src = join(__dirname, "node_modules/purecss/build/pure-min.css");
const destDir = join(__dirname, "src/camille/static/dist");
const dest = join(destDir, "pure-min.css");

async function build() {
    try {
        await mkdir(destDir, { recursive: true });
        await copyFile(src, dest);
        console.log("Copied pure-min.css to dist directory.");
    } catch (err) {
        console.error("Error copying file:", err);
    }
}

build();

// Watch for changes in node_modules/purecss/build/pure-min.css and copy it again if it changes
watch(src, (eventType) => {
    if (eventType === "change") {
        console.log("pure-min.css changed, copying again...");
        build();
    }
});
