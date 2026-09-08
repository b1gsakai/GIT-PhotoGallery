const cards = document.querySelectorAll(".card");
const status = document.querySelector(".selection-status");

function selectCard(card) {
    cards.forEach((item) => item.classList.remove("is-selected"));
    card.classList.add("is-selected");
    status.textContent = `Selected: ${card.dataset.title}`;
}

cards.forEach((card) => {
    card.addEventListener("click", () => selectCard(card));
    card.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            selectCard(card);
        }
    });
});