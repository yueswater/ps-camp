document.addEventListener('DOMContentLoaded', () => {
    console.log("new_post.js loaded");
    
    // 可擴充功能：自動聚焦標題欄位
    const titleInput = document.getElementById("title");
    if (titleInput) titleInput.focus();
});
