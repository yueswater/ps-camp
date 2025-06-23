let showTimer = null;
let hideTimer = null;

function scheduleShowPopup(event) {
  const region = event.currentTarget;
  showTimer = setTimeout(() => openPopup(region), 500);
}

function cancelShowPopup() {
  clearTimeout(showTimer);
  scheduleClosePopup();
}

function openPopup(region) {
  const popup = document.getElementById('map-popup');
  document.getElementById('popup-name').textContent = region.dataset.name;
  document.getElementById('popup-detail').textContent = region.dataset.detail;
  popup.classList.add('show');
}

function closePopup() {
  clearTimeout(showTimer);
  clearTimeout(hideTimer);
  const popup = document.getElementById('map-popup');
  popup.classList.remove('show');
  setTimeout(() => {
    popup.style.display = 'none';
  }, 250);
}

function scheduleClosePopup() {
  hideTimer = setTimeout(closePopup, 100);
}

function cancelAutoClose() {
  clearTimeout(hideTimer);
}
