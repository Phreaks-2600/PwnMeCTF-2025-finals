const express = require("express");

const app = express();
app.use(express.json());

app.post("/comment", async (req, res) => {
    const url = req.body.url;
    if (!url) {
        return res.status(400).send("URL is required");
    }

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.text();
        res.send(data);
    } catch (error) {
        console.error("Error fetching URL:", error);
        res.status(500).send("Error fetching URL");
    }
});

app.listen(5000, () => {
    console.log("Node.js proxy server running on http://localhost:5000");
});