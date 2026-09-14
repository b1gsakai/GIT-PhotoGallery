const cards = document.querySelectorAll(".card");
const status = document.querySelector(".selection-status");
const COOLDOWN_SECONDS = 10;

function getStorageKey(card) {
    const image = card.querySelector("img")?.src;
    const title = card.dataset.title || card.querySelector("h2")?.textContent || "";
    return `description:${title}:${image}`;
}

function restoreSavedDescriptions() {
    cards.forEach((card) => {
        const storageKey = getStorageKey(card);
        const savedDescription = localStorage.getItem(storageKey);
        if (savedDescription) {
            const details = card.querySelector(".card-description");
            const output = details?.querySelector("p");
            if (output) {
                output.textContent = savedDescription;
            }
        }
    });
}

function selectCard(card) {
    cards.forEach((item) => item.classList.remove("is-selected"));
    card.classList.add("is-selected");
    status.textContent = `Selected: ${card.dataset.title}`;
}

async function generateDescription(card, button, output) {
    const image = card.querySelector("img");
    const title = card.dataset.title || card.querySelector("h2")?.textContent || "";
    const storageKey = getStorageKey(card);

    button.disabled = true;
    button.textContent = "Generating…";
    const currentText = output.textContent;
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
        localStorage.setItem(storageKey, result.description);
        status.textContent = `AI description ready for ${title}`;

        // Start cooldown timer
        let cooldown = COOLDOWN_SECONDS;
        button.textContent = `Wait ${cooldown}s…`;
        const timer = setInterval(() => {
            cooldown--;
            button.textContent = `Wait ${cooldown}s…`;
            if (cooldown <= 0) {
                clearInterval(timer);
                button.disabled = false;
                button.textContent = "Generate with Groq";
            }
        }, 1000);
    } catch (error) {
        output.textContent = currentText;
        status.textContent = error.message;
        button.disabled = false;
        button.textContent = "Generate with Groq";
    }
}

// Restore saved descriptions on page load
restoreSavedDescriptions();

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