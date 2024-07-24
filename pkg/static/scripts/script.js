"use strict";

const categoriesButton = document.querySelector(".categoriesButton");
const categories = document.querySelector(".categories");

categoriesButton.addEventListener("mouseover", () => {
  categories.classList.remove("hidden");
});

categoriesButton.addEventListener("mouseout", () => {
  categories.classList.add("hidden");
});

categories.addEventListener("mouseover", () => {
  categories.classList.remove("hidden");
});

categories.addEventListener("mouseout", () => {
  categories.classList.add("hidden");
});

// Contact modal
const modal = document.getElementById("contactModal");
const btn = document.getElementById("contactButton");
const span = document.getElementsByClassName("close")[0];

btn.onclick = function () {
  modal.style.display = "block";
};

span.onclick = function () {
  modal.style.display = "none";
};

window.onclick = function (event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
};
