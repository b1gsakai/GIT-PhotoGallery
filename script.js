const cards = document.querySelectorAll(".card");
const status = document.querySelector(".selection-status");

function selectCard(card) {
    cards.forEach((item) => item.classList.remove("is-selected"));
    card.classList.add("is-selected");
    status.textContent = `Selected: ${card.dataset.title}`;
}

async function generateDescription(card, button, output) {
    const image = card.querySelector("img");
    const title = card.dataset.title || card.querySelector("h2")?.textContent || "";
    const originalText = output.dataset.original || output.textContent;

    button.disabled = true;
    button.textContent = "Generating…";
    output.dataset.original = originalText;
    output.textContent = "Generating an AI description…";

    try {
        const response = await fetch("/api/describe", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ imageUrl: image.src, title }),
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || "Description generation failed.");
        }
        output.textContent = result.description;
        status.textContent = `AI description ready for ${title}`;
    } catch (error) {
        output.textContent = originalText;
        status.textContent = error.message;
    } finally {
        button.disabled = false;
        button.textContent = "Generate with Groq";
    }
}

cards.forEach((card) => {
    card.addEventListener("click", () => selectCard(card));
    card.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            selectCard(card);
        }
    });

    const details = card.querySelector(".card-description");
    const output = details?.querySelector("p");
    if (details && output) {
        const button = document.createElement("button");
        button.className = "generate-description";
        button.type = "button";
        button.textContent = "Generate with Groq";
        button.addEventListener("click", (event) => {
            event.stopPropagation();
            generateDescription(card, button, output);
        });
        details.insertBefore(button, output);
    }
});