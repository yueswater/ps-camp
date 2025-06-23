/* timers */
let showTimer = null, hideTimer = null;

/* when mouse enters card */
function scheduleShowPopup(e) {
    const card = e.currentTarget;
    showTimer = setTimeout(() => openPopup(card), 700);
}

/* if mouse leaves card */
function cancelShowPopup() {
    clearTimeout(showTimer);
    scheduleClosePopup();
}

/* open popup */
function openPopup(card) {
    const pop = document.getElementById('npc-popup');
    document.getElementById('popup-name').textContent = card.dataset.name;
    document.getElementById('popup-title').textContent = card.dataset.title;
    document.getElementById('popup-detail').textContent = card.dataset.detail;
    pop.classList.add('show');
}

/* schedule hide quickly */
function scheduleClosePopup() {
    hideTimer = setTimeout(closePopup, 100);
}

/* keep popup if cursor over it */
function cancelAutoClose() { clearTimeout(hideTimer); }

/* close popup immediately */
function closePopup() {
    clearTimeout(showTimer); clearTimeout(hideTimer);
    const pop = document.getElementById('npc-popup');
    pop.classList.remove('show');
    /* CSS transition hides visual; display reset after */
    setTimeout(() => { pop.style.display = 'none'; pop.style.display = ''; }, 250);
}
