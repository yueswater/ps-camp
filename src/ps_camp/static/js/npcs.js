function goToNpc(name) {
    const encodedName = encodeURIComponent(name);
    window.location.href = `/npc/${encodedName}`;
}
