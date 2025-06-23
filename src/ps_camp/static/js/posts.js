//JavaScript for post pages -Threads style interaction

document.addEventListener('DOMContentLoaded', function () {
    initPostInteractions();
    initInfiniteScroll();
    initPostAnimations();
    initCategoryStyles();
    markActiveCategory();  //Add to this line: mark the selected category

    console.log("貼文頁面功能載入完成");
});

document.addEventListener("click", function (e) {
    if (e.target.classList.contains("read-more")) {
        e.preventDefault();
        const postId = e.target.dataset.postId;
        fetch(`/api/posts/${postId}`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const previewEl = document.querySelector(`.preview[data-post-id="${postId}"]`);
                    previewEl.innerHTML = data.content;
                }
            });
    }
});

function initPostInteractions() {
    //Like button function
    document.querySelectorAll('.like-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const postId = btn.closest('.post-card').dataset.postId;

            fetch(`/api/posts/${postId}/like`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        btn.querySelector('span').innerText = data.likes;
                        btn.classList.toggle('liked');

                        const postCard = btn.closest('.post-card');
                        const statsItems = postCard.querySelectorAll('.stats-item');
                        statsItems.forEach(item => {
                            if (item.textContent.includes('個讚')) {
                                item.textContent = `${data.likes} 個讚`;
                            }
                        });
                    }
                });
        });
    });


    //Reply button function
    document.querySelectorAll('.comment-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            showCommentModal(this);
        });
    });

    //Share button function
    document.querySelectorAll('.share-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            sharePost(this);
        });
    });

    //Favorite button function
    document.querySelectorAll('.bookmark-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            toggleBookmark(this);
        });
    });

    //Filter classification button function (change URL dynamically)
    document.querySelectorAll('.filter-tag').forEach(button => {
        button.addEventListener('click', function () {
            const category = this.dataset.category;
            const url = new URL(window.location.href);
            const current = url.searchParams.get('category');

            if (current === category) {
                url.searchParams.delete('category'); //Cancel filter
            } else {
                url.searchParams.set('category', category);
            }
            window.location.href = url.toString();
        });
    });
}

function markActiveCategory() {
    const url = new URL(window.location.href);
    const currentCategory = url.searchParams.get("category");

    document.querySelectorAll(".filter-tag").forEach(btn => {
        if (btn.dataset.category === currentCategory) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });
}

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

function updateLikeCount(statsElement, change) {
    if (!statsElement) return;

    const currentText = statsElement.textContent;
    const currentCount = parseInt(currentText.match(/\d+/)[0]) || 0;
    const newCount = Math.max(0, currentCount + change);

    statsElement.textContent = `${newCount} 個讚`;
}

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

function showCommentModal(button) {
    const postCard = button.closest('.post-card');
    const postTitle = postCard.querySelector('.post-title').textContent;

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

    setTimeout(() => {
        modal.classList.add('show');
    }, 10);

    modal.querySelector('.modal-close').addEventListener('click', () => closeModal(modal));
    modal.querySelector('.modal-cancel').addEventListener('click', () => closeModal(modal));
    modal.querySelector('.modal-overlay').addEventListener('click', (e) => {
        if (e.target === modal.querySelector('.modal-overlay')) {
            closeModal(modal);
        }
    });

    modal.querySelector('.comment-submit').addEventListener('click', () => {
        const comment = modal.querySelector('.comment-input').value.trim();
        if (comment) {
            const commentBtn = button;
            const commentSpan = commentBtn.querySelector('span');
            if (commentSpan) {
                const currentCount = parseInt(commentSpan.textContent) || 0;
                commentSpan.textContent = currentCount + 1;
            }

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

    modal.querySelector('.comment-input').focus();
}

function closeModal(modal) {
    modal.classList.remove('show');
    setTimeout(() => {
        modal.remove();
    }, 300);
}

function sharePost(button) {
    const postCard = button.closest('.post-card');
    const postTitle = postCard.querySelector('.post-title').textContent;
    const postContent = postCard.querySelector('.post-text').textContent;

    const shareSpan = button.querySelector('span');
    if (shareSpan) {
        const currentCount = parseInt(shareSpan.textContent) || 0;
        shareSpan.textContent = currentCount + 1;
    }

    const statsItems = postCard.querySelectorAll('.stats-item');
    statsItems.forEach(item => {
        if (item.textContent.includes('分享')) {
            const currentCount = parseInt(item.textContent.match(/\d+/)[0]) || 0;
            item.textContent = `${currentCount + 1} 次分享`;
        }
    });

    if (navigator.share) {
        navigator.share({
            title: postTitle,
            text: postContent,
            url: window.location.href
        }).then(() => {
            showNotification('分享成功', 'success');
        }).catch(() => {
            if (shareSpan) {
                const currentCount = parseInt(shareSpan.textContent) || 0;
                shareSpan.textContent = Math.max(0, currentCount - 1);
            }
        });
    } else {
        const shareText = `${postTitle}\n\n${postContent}\n\n來自沙政風暴`;
        navigator.clipboard.writeText(shareText).then(() => {
            showNotification('連結已複製到剪貼板', 'success');
        }).catch(() => {
            showNotification('分享功能暫時無法使用', 'error');
            if (shareSpan) {
                const currentCount = parseInt(shareSpan.textContent) || 0;
                shareSpan.textContent = Math.max(0, currentCount - 1);
            }
        });
    }
}

function initInfiniteScroll() {
    const loadMoreBtn = document.querySelector('.load-more-btn');
    if (!loadMoreBtn) return;

    const hasNextPage = document.body.dataset.hasNextPage === 'true';
    if (!hasNextPage) {
        loadMoreBtn.remove();              // 沒下一頁→整顆按鈕不顯示
        return;
    }

    // 讓按鈕先顯示（出現在畫面下方）
    loadMoreBtn.classList.remove('hidden');

    loadMoreBtn.addEventListener('click', () => loadMorePosts(loadMoreBtn));

    window.addEventListener(
        'scroll',
        debounce(() => {
            // 捲到離底 800px 內就自動觸發一次
            if (
                window.innerHeight + window.scrollY >=
                document.body.offsetHeight - 800
            ) {
                loadMorePosts(loadMoreBtn);
            }
        }, 250)
    );
}

function loadMorePosts(button) {
  if (button.classList.contains('loading')) return;

  button.classList.add('loading');
  button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 載入中…';

  // 這裡用 fetch 真的去撈下一頁（範例以 setTimeout 假裝）
  setTimeout(() => {
    /* ===== 這裡換成你實際插入新貼文的程式 ===== */
    // 假設從伺服器得知「已經沒有下一頁」
    const noMore = true; // ← 把這判斷改成你的 API 回傳

    if (noMore) {
      button.remove();                // 移除按鈕，不再顯示
    } else {
      button.classList.remove('loading');
      button.innerHTML =
        '<i class="fas fa-chevron-down"></i> 載入更多貼文';
    }

    showNotification('已載入更多貼文', 'info');
  }, 1500);
}

function initPostAnimations() {
    const posts = document.querySelectorAll('.post-card');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, index * 50);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    posts.forEach((post, index) => {
        post.style.opacity = '0';
        post.style.transform = 'translateY(10px)';
        post.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        observer.observe(post);
    });
}

function initCategoryStyles() {
    document.querySelectorAll('.category-tag').forEach(tag => {
        const category = tag.textContent.toLowerCase().trim();

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

function showNotification(message, type) {
    if (window.SandstormApp && window.SandstormApp.showNotification) {
        window.SandstormApp.showNotification(message, type);
    } else {
        console.log(`${type}: ${message}`);
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
