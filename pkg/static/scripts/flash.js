"use strict";

document.addEventListener("DOMContentLoaded", function () {
  const flashMessageContainer = document.querySelector(
    ".flashMessageContainerDisplay"
  );
  const flashMessages = flashMessageContainer.querySelector(".flash-messages");

  if (flashMessages) {
    flashMessageContainer.style.display = "block";
    setTimeout(() => {
      flashMessageContainer.style.opacity = 1;
    }, 100);

    setTimeout(() => {
      flashMessageContainer.style.opacity = 0;
      setTimeout(() => {
        flashMessageContainer.style.display = "none";
      }, 500);
    }, 5000);
  }
});
