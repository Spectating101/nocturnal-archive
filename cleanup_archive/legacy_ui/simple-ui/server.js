const http = require("http");
const fs = require("fs");
const path = require("path");

const server = http.createServer((req, res) => {
  let filePath = "";

  if (req.url === "/") {
    filePath = path.join(__dirname, "enhanced.html"); // Use the enhanced UI by default
  } else if (req.url === "/simple") {
    filePath = path.join(__dirname, "index.html"); // Original simple UI at /simple
  } else {
    res.writeHead(404);
    res.end("Not found");
    return;
  }

  fs.readFile(filePath, (err, content) => {
    if (err) {
      res.writeHead(500);
      res.end("Error loading page");
      return;
    }
    res.writeHead(200, { "Content-Type": "text/html" });
    res.end(content);
  });
});

server.listen(3001, () => {
  console.log("Nocturnal Archive UI running at http://localhost:3001");
  console.log("Simple UI available at http://localhost:3001/simple");
});
