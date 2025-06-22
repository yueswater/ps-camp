// 貼文頁面專用 JavaScript - Threads 風格互動

// 當 DOM 載入完成後執行
document.addEventListener('DOMContentLoaded', function() {
    initPostInteractions();
    initInfiniteScroll();
    initPostAnimations();
    initCategoryStyles();
    
    console.log("貼文頁面功能載入完成");
});

// 初始化貼文互動功能
function initPostInteractions() {
    // 喜歡按鈕功能
    document.querySelectorAll('.like-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            toggleLike(this);
        });
    });

    // 回覆按鈕功能
    document.querySelectorAll('.comment-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            showCommentModal(this);
        });
    });

    // 分享按鈕功能
    document.querySelectorAll('.share-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            sharePost(this);
        });
    });

    // 收藏按鈕功能
    document.querySelectorAll('.bookmark-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            toggleBookmark(this);
        });
    });

    // 篩選與搜尋功能
    const filterBtn = document.querySelector('.posts-filter button');
    if (filterBtn) {
        filterBtn.addEventListener('click', function (e) {
            e.preventDefault();
            const category = document.getElementById('categoryFilter').value;
            const keyword = document.getElementById('postSearch').value;

            const url = new URL(window.location.href);
            url.searchParams.set('category', category);
            url.searchParams.set('search', keyword);
            window.location.href = url.toString();
        });
    }
}

// 切換喜歡狀態
function toggleLike(button) {
    const postCard = button.closest('.post-card');
    const postId = postCard.dataset.postId;
    const isLiked = button.classList.contains('active');

    fetch(`/api/posts/${postId}/like`, {
        method: isLiked ? 'DELETE' : 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(res => res.json())
      .then(data => {
        if (data.success) {
            const icon = button.querySelector('i');
            const text = button.querySelector('span');
            const statsItem = postCard.querySelector('.stats-item');

            button.classList.toggle('active');
            icon.className = isLiked ? 'far fa-heart' : 'fas fa-heart';

            if (text) {
                text.textContent = data.likes;
            }
            if (statsItem) {
                statsItem.textContent = `${data.likes} 個讚`;
            }

            if (!isLiked) {
                button.classList.add('animating');
                setTimeout(() => {
                    button.classList.remove('animating');
                }, 300);
            }
        } else {
            showNotification(data.message || '操作失敗', 'error');
        }
    }).catch(() => {
        showNotification('無法連線到伺服器', 'error');
    });
}


// 更新喜歡數量
function updateLikeCount(statsElement, change) {
    if (!statsElement) return;
    
    const currentText = statsElement.textContent;
    const currentCount = parseInt(currentText.match(/\d+/)[0]) || 0;
    const newCount = Math.max(0, currentCount + change);
    
    statsElement.textContent = `${newCount} 個讚`;
}

// 切換收藏狀態
function toggleBookmark(button) {
    const isBookmarked = button.classList.contains('active');
    const icon = button.querySelector('i');
    
    if (isBookmarked) {
        button.classList.remove('active');
        icon.className = 'far fa-bookmark';
        showNotification('已取消收藏', 'info');
    } else {
        button.classList.add('active');
        icon.className = 'fas fa-bookmark';
        showNotification('已收藏貼文', 'success');
    }
}

// 顯示回覆模態框
function showCommentModal(button) {
    const postCard = button.closest('.post-card');
    const postTitle = postCard.querySelector('.post-title').textContent;
    
    // 創建模態框
    const modal = document.createElement('div');
    modal.className = 'comment-modal';
    modal.innerHTML = `
        <div class="modal-overlay">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>回覆貼文</h3>
                    <button class="modal-close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <p class="original-post">回覆：${postTitle}</p>
                    <textarea placeholder="寫下你的回覆..." class="comment-input"></textarea>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-outline modal-cancel">取消</button>
                    <button class="btn btn-primary comment-submit">
                        <i class="fas fa-paper-plane"></i> 發送回覆
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 顯示動畫
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
    
    // 關閉功能
    modal.querySelector('.modal-close').addEventListener('click', () => closeModal(modal));
    modal.querySelector('.modal-cancel').addEventListener('click', () => closeModal(modal));
    modal.querySelector('.modal-overlay').addEventListener('click', (e) => {
        if (e.target === modal.querySelector('.modal-overlay')) {
            closeModal(modal);
        }
    });
    
    // 發送回覆
    modal.querySelector('.comment-submit').addEventListener('click', () => {
        const comment = modal.querySelector('.comment-input').value.trim();
        if (comment) {
            // 更新回覆數量
            const commentBtn = button;
            const commentSpan = commentBtn.querySelector('span');
            if (commentSpan) {
                const currentCount = parseInt(commentSpan.textContent) || 0;
                commentSpan.textContent = currentCount + 1;
            }
            
            // 更新統計
            const statsItems = postCard.querySelectorAll('.stats-item');
            statsItems.forEach(item => {
                if (item.textContent.includes('回覆')) {
                    const currentCount = parseInt(item.textContent.match(/\d+/)[0]) || 0;
                    item.textContent = `${currentCount + 1} 則回覆`;
                }
            });
            
            showNotification('回覆已發送', 'success');
            closeModal(modal);
        } else {
            showNotification('請輸入回覆內容', 'warning');
        }
    });
    
    // 聚焦到輸入框
    modal.querySelector('.comment-input').focus();
}

// 關閉模態框
function closeModal(modal) {
    modal.classList.remove('show');
    setTimeout(() => {
        modal.remove();
    }, 300);
}

// 分享貼文功能
function sharePost(button) {
    const postCard = button.closest('.post-card');
    const postTitle = postCard.querySelector('.post-title').textContent;
    const postContent = postCard.querySelector('.post-text').textContent;
    
    // 更新分享數量
    const shareSpan = button.querySelector('span');
    if (shareSpan) {
        const currentCount = parseInt(shareSpan.textContent) || 0;
        shareSpan.textContent = currentCount + 1;
    }
    
    // 更新統計
    const statsItems = postCard.querySelectorAll('.stats-item');
    statsItems.forEach(item => {
        if (item.textContent.includes('分享')) {
            const currentCount = parseInt(item.textContent.match(/\d+/)[0]) || 0;
            item.textContent = `${currentCount + 1} 次分享`;
        }
    });
    
    // 檢查是否支援 Web Share API
    if (navigator.share) {
        navigator.share({
            title: postTitle,
            text: postContent,
            url: window.location.href
        }).then(() => {
            showNotification('分享成功', 'success');
        }).catch(() => {
            // 如果用戶取消分享，還原數字
            if (shareSpan) {
                const currentCount = parseInt(shareSpan.textContent) || 0;
                shareSpan.textContent = Math.max(0, currentCount - 1);
            }
        });
    } else {
        // 降級處理：複製到剪貼板
        const shareText = `${postTitle}\n\n${postContent}\n\n來自沙政風暴`;
        navigator.clipboard.writeText(shareText).then(() => {
            showNotification('連結已複製到剪貼板', 'success');
        }).catch(() => {
            showNotification('分享功能暫時無法使用', 'error');
            // 還原數字
            if (shareSpan) {
                const currentCount = parseInt(shareSpan.textContent) || 0;
                shareSpan.textContent = Math.max(0, currentCount - 1);
            }
        });
    }
}

// 無限滾動載入
function initInfiniteScroll() {
    const loadMoreBtn = document.querySelector('.load-more-btn');
    
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', function() {
            loadMorePosts(this);
        });
        
        // 自動載入（當滾動到接近底部時）
        window.addEventListener('scroll', debounce(() => {
            if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 1000) {
                loadMorePosts(loadMoreBtn);
            }
        }, 250));
    }
}

// 載入更多貼文
function loadMorePosts(button) {
    if (button.classList.contains('loading')) return;
    
    button.classList.add('loading');
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 載入中...';
    
    // 模擬 API 請求
    setTimeout(() => {
        // 這裡應該是實際的 API 請求
        showNotification('已載入更多貼文', 'info');
        
        button.classList.remove('loading');
        button.innerHTML = '<i class="fas fa-chevron-down"></i> 載入更多貼文';
    }, 1500);
}

// 初始化貼文動畫
function initPostAnimations() {
    const posts = document.querySelectorAll('.post-card');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, index * 50); // 減少延遲時間
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    posts.forEach((post, index) => {
        post.style.opacity = '0';
        post.style.transform = 'translateY(10px)'; // 減少移動距離
        post.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        
        observer.observe(post);
    });
}

// 初始化分類樣式
function initCategoryStyles() {
    document.querySelectorAll('.category-tag').forEach(tag => {
        const category = tag.textContent.toLowerCase().trim();
        
        // 根據分類添加對應的 CSS 類別
        if (category.includes('政治') || category.includes('政策')) {
            tag.classList.add('politics');
        } else if (category.includes('經濟') || category.includes('財政')) {
            tag.classList.add('economy');
        } else if (category.includes('社會') || category.includes('民生')) {
            tag.classList.add('social');
        } else if (category.includes('公告') || category.includes('重要')) {
            tag.classList.add('announcement');
        }
    });
}

// 貼文搜尋功能
function initPostSearch() {
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.placeholder = '搜尋貼文...';
    searchInput.className = 'post-search';
    
    const postsHeader = document.querySelector('.posts-header');
    if (postsHeader) {
        postsHeader.insertBefore(searchInput, postsHeader.querySelector('.posts-actions'));
    }
    
    searchInput.addEventListener('input', debounce((e) => {
        filterPosts(e.target.value);
    }, 300));
}

// 過濾貼文
function filterPosts(searchTerm) {
    const posts = document.querySelectorAll('.post-card');
    const term = searchTerm.toLowerCase();
    
    posts.forEach(post => {
        const title = post.querySelector('.post-title').textContent.toLowerCase();
        const content = post.querySelector('.post-text').textContent.toLowerCase();
        const author = post.querySelector('.author-name').textContent.toLowerCase();
        
        const matches = title.includes(term) || content.includes(term) || author.includes(term);
        
        post.style.display = matches ? 'block' : 'none';
    });
}

// 工具函數：防抖
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

// 通知功能（使用全域的 showNotification 或降級處理）
function showNotification(message, type) {
    if (window.SandstormApp && window.SandstormApp.showNotification) {
        window.SandstormApp.showNotification(message, type);
    } else {
        // 簡單的降級處理
        console.log(`${type}: ${message}`);
        
        // 創建簡單通知
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem;
            background: #007bff;
            color: white;
            border-radius: 8px;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        
        if (type === 'success') notification.style.background = '#28a745';
        if (type === 'error') notification.style.background = '#dc3545';
        if (type === 'warning') notification.style.background = '#ffc107';
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => notification.style.opacity = '1', 100);
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}