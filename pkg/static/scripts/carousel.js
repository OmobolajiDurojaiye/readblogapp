"use strict";

const track = document.querySelector(".carousel-track");
const slides = Array.from(track.children);
const nextButton = document.querySelector(".carousel-next");
const prevButton = document.querySelector(".carousel-prev");

let slideIndex = 0;

function moveToSlide(track, currentSlide, targetSlide) {
  track.style.transform = `translateX(-${targetSlide.style.left})`;
  currentSlide.classList.remove("current-slide");
  targetSlide.classList.add("current-slide");
}

function updateSlidePosition() {
  const slideWidth = slides[0].getBoundingClientRect().width;
  slides.forEach((slide, index) => {
    slide.style.left = slideWidth * index + "px";
  });
}

function autoSlide() {
  setInterval(() => {
    slideIndex = (slideIndex + 1) % slides.length;
    const currentSlide = track.querySelector(".current-slide");
    const nextSlide = slides[slideIndex];
    moveToSlide(track, currentSlide, nextSlide);
  }, 5000); // Adjust the time interval (5000ms = 5 seconds)
}

nextButton.addEventListener("click", () => {
  slideIndex = (slideIndex + 1) % slides.length;
  const currentSlide = track.querySelector(".current-slide");
  const nextSlide = slides[slideIndex];
  moveToSlide(track, currentSlide, nextSlide);
});

prevButton.addEventListener("click", () => {
  slideIndex = (slideIndex - 1 + slides.length) % slides.length;
  const currentSlide = track.querySelector(".current-slide");
  const prevSlide = slides[slideIndex];
  moveToSlide(track, currentSlide, prevSlide);
});

window.addEventListener("load", () => {
  slides[0].classList.add("current-slide");
  updateSlidePosition();
  autoSlide();
});
