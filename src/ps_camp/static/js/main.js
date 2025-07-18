// 沙政風暴網站主要 JavaScript 檔案
console.log("沙政風暴網站載入完畢");

// DOM 載入完成後執行
document.addEventListener('DOMContentLoaded', function() {

    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
        setTimeout(() => {
            loadingScreen.style.display = 'none';
        }, 400);
    }

    
    // 初始化功能
    initSmoothScrolling();
    initFormValidation();
    initCardAnimations();
    initNavigation();
    initMobileMenu();
    
    console.log("所有功能初始化完成");
});

// 平滑滾動功能
function initSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// 表單驗證功能
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('input[required], textarea[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    showFieldError(field, '此欄位為必填');
                } else {
                    clearFieldError(field);
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showNotification('請填寫所有必填欄位', 'error');
            }
        });
        
        // 即時驗證
        const inputs = form.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.hasAttribute('required') && !this.value.trim()) {
                    showFieldError(this, '此欄位為必填');
                } else {
                    clearFieldError(this);
                }
            });
        });
    });
}

// 顯示欄位錯誤
function showFieldError(field, message) {
    clearFieldError(field);
    
    field.style.borderColor = '#dc3545';
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.style.color = '#dc3545';
    errorDiv.style.fontSize = '0.875rem';
    errorDiv.style.marginTop = '0.25rem';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

// 清除欄位錯誤
function clearFieldError(field) {
    field.style.borderColor = '#e9ecef';
    
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

// 卡片動畫效果
function initCardAnimations() {
    const cards = document.querySelectorAll('.card, .list-item');
    
    // 使用 Intersection Observer 來觸發動畫
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1
    });
    
    cards.forEach((card, index) => {
        // 初始隱藏狀態
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
        
        observer.observe(card);
    });
}

// 導航功能
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const currentPath = window.location.pathname;
    
    // 高亮當前頁面
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.backgroundColor = '#e9ecef';
            link.style.color = '#212529';
        }
    });
}

// 手機版選單功能
function initMobileMenu() {
    const menuToggle = document.querySelector('.mobile-menu-toggle');
    const navbar = document.querySelector('.navbar');
    const overlay = document.querySelector('.mobile-overlay');
    const navLinks = document.querySelectorAll('.nav-link');
    
    if (!menuToggle || !navbar || !overlay) {
        return; // 如果元素不存在就直接返回
    }
    
    // 切換選單狀態
    function toggleMenu() {
        const isActive = navbar.classList.contains('active');
        
        if (isActive) {
            closeMenu();
        } else {
            openMenu();
        }
    }
    
    // 打開選單
    function openMenu() {
        navbar.classList.add('active');
        overlay.classList.add('active');
        menuToggle.classList.add('active');
        document.body.style.overflow = 'hidden'; // 防止背景滾動
    }
    
    // 關閉選單
    function closeMenu() {
        navbar.classList.remove('active');
        overlay.classList.remove('active');
        menuToggle.classList.remove('active');
        document.body.style.overflow = ''; // 恢復滾動
    }
    
    // 點擊漢堡選單按鈕
    menuToggle.addEventListener('click', function(e) {
        e.stopPropagation();
        toggleMenu();
    });
    
    // 點擊遮罩關閉選單
    overlay.addEventListener('click', closeMenu);
    
    // 點擊導航連結後關閉選單
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            // 延遲關閉，讓頁面跳轉效果更順暢
            setTimeout(closeMenu, 150);
        });
    });
    
    // 窗口大小變化時的處理
    window.addEventListener('resize', debounce(function() {
        if (window.innerWidth > 768) {
            // 大螢幕時關閉手機選單
            closeMenu();
        }
    }, 250));
    
    // ESC 鍵關閉選單
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && navbar.classList.contains('active')) {
            closeMenu();
        }
    });
    
    // 防止選單內部點擊事件冒泡
    navbar.addEventListener('click', function(e) {
        e.stopPropagation();
    });
    
    // 觸控手勢支援（簡單的左滑關閉）
    let touchStartX = 0;
    let touchEndX = 0;
    
    navbar.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    });
    
    navbar.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    });
    
    function handleSwipe() {
        const swipeDistance = touchEndX - touchStartX;
        const minSwipeDistance = 50;
        
        // 左滑關閉選單
        if (swipeDistance < -minSwipeDistance && navbar.classList.contains('active')) {
            closeMenu();
        }
    }
}

// 通知功能
function showNotification(message, type = 'info') {
    // 移除現有通知
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // 創建新通知
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        max-width: 300px;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
    `;
    
    // 根據類型設定顏色
    switch(type) {
        case 'success':
            notification.style.backgroundColor = '#28a745';
            break;
        case 'error':
            notification.style.backgroundColor = '#dc3545';
            break;
        case 'warning':
            notification.style.backgroundColor = '#ffc107';
            notification.style.color = '#212529';
            break;
        default:
            notification.style.backgroundColor = '#007bff';
    }
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // 顯示動畫
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // 自動隱藏
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// 載入狀態管理
function showLoading() {
    const loader = document.createElement('div');
    loader.className = 'loading-overlay';
    loader.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    `;
    
    loader.innerHTML = `
        <div style="
            width: 40px;
            height: 40px;
            border: 4px solid #e9ecef;
            border-top: 4px solid #007bff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        "></div>
        <style>
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    `;
    
    document.body.appendChild(loader);
}

function hideLoading() {
    const loader = document.querySelector('.loading-overlay');
    if (loader) {
        loader.remove();
    }
}

// 工具函數
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 格式化日期
function formatDate(date) {
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(date).toLocaleDateString('zh-TW', options);
}

// 截斷文字
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// 導出功能供其他腳本使用
window.SandstormApp = {
    showNotification,
    showLoading,
    hideLoading,
    debounce,
    formatDate,
    truncateText
};