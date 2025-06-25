// 移除 mockData，改為從 API 獲取真實數據
let currentData = null;

function formatNumber(num) {
    if (num >= 10000) {
        const wan = Math.floor(num / 10000);
        const remainder = num % 10000;
        return {
            main: wan,
            unit: '萬',
            sub: remainder > 0 ? remainder.toString().padStart(4, '0') : ''
        };
    }
    return {
        main: num,
        unit: '',
        sub: ''
    };
}

// 從後端 API 獲取投票結果
async function fetchVoteResults() {
    try {
        const response = await fetch('/api/live_votes'); // 使用正確的 API endpoint
        if (!response.ok) {
            throw new Error('Failed to fetch vote results');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching vote results:', error);
        // 如果 API 失敗，返回空數據結構
        return {
            timestamp: new Date().toISOString(),
            votes: {
                party_votes: {},
                party_names: {},
                referendum_votes: { yes: 0, no: 0 }
            }
        };
    }
}

async function updateResults() {
    // 獲取最新數據
    currentData = await fetchVoteResults();
    const data = currentData;
    
    // 更新時間戳
    const timestamp = new Date(data.timestamp);
    const timestampElement = document.getElementById('last-update');
    if (timestampElement) {
        timestampElement.textContent = timestamp.toLocaleString('zh-TW');
    }

    // 處理政黨票
    const partyVotes = data.votes.party_votes || {};
    const partyNames = data.votes.party_names || {};
    const totalPartyVotes = Object.values(partyVotes).reduce((a, b) => a + b, 0);

    // 更新統計卡片
    const totalVotesElement = document.getElementById('total-votes');
    const turnoutElement = document.getElementById('turnout');
    const leadingPartyElement = document.getElementById('leading-party');
    
    if (totalVotesElement) {
        totalVotesElement.textContent = totalPartyVotes.toLocaleString();
    }
    
    if (turnoutElement) {
        // 你可以從後端傳送真實的投票率，或者根據總投票數計算
        const estimatedTurnout = data.votes.turnout || '計算中';
        turnoutElement.textContent = typeof estimatedTurnout === 'number' ? 
            `${estimatedTurnout.toFixed(1)}%` : estimatedTurnout;
    }
    
    // 找出領先政黨
    if (leadingPartyElement && Object.keys(partyVotes).length > 0) {
        const leadingParty = Object.entries(partyVotes).reduce((a, b) => a[1] > b[1] ? a : b);
        leadingPartyElement.textContent = partyNames[leadingParty[0]] || '計算中';
    }

    // 渲染政黨票結果 - 新的卡片式設計
    const partyContainer = document.getElementById('party-results');
    if (partyContainer) {
        partyContainer.innerHTML = '';
        partyContainer.className = 'party-grid'; // 設定為網格佈局

        // 按票數排序
        const sortedParties = Object.entries(partyVotes)
            .sort(([,a], [,b]) => b - a);

        sortedParties.forEach(([partyId, count]) => {
            const name = partyNames[partyId] || partyId;
            const percent = totalPartyVotes > 0 ? ((count / totalPartyVotes) * 100).toFixed(1) : "0.0";
            const formatted = formatNumber(count);

            const item = document.createElement('div');
            item.className = 'party-card'; // 改為 party-card
            item.innerHTML = `
                <div class="party-card-header">
                    <div class="party-name">${name}</div>
                    <div class="percentage-badge">${percent}%</div>
                </div>
                <div class="vote-count">
                    <span class="count-main">${formatted.main.toLocaleString()}</span>
                    <span class="count-unit">${formatted.unit}</span>
                    ${formatted.sub ? `<span class="count-sub">${formatted.sub}</span>` : ''}
                </div>
                <div class="vote-details">
                    <div class="detail-item">
                        <span class="detail-label">得票數</span>
                        <span class="detail-value">${count.toLocaleString()}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">席次</span>
                        <span class="detail-value">${data.votes.seats && data.votes.seats[partyId] ? data.votes.seats[partyId] : '待計算'}</span>
                    </div>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${percent}%"></div>
                </div>
            `;
            partyContainer.appendChild(item);
        });
    }

    // 處理公投票 - 保持原來的樣式
    const refVotes = data.votes.referendum_votes || {};
    const totalRefVotes = (refVotes.yes || 0) + (refVotes.no || 0);

    const refContainer = document.getElementById('referendum-results');
    if (refContainer) {
        refContainer.innerHTML = '';

        const refOptions = [
            { key: 'yes', label: '同意', class: 'agree', icon: 'fas fa-check' },
            { key: 'no', label: '不同意', class: 'disagree', icon: 'fas fa-times' }
        ];

        refOptions.forEach(({ key, label, class: className, icon }) => {
            const count = refVotes[key] || 0;
            const percent = totalRefVotes > 0 ? ((count / totalRefVotes) * 100).toFixed(1) : "0.0";
            const formatted = formatNumber(count);

            const item = document.createElement('div');
            item.className = `vote-item ${className}`;
            item.innerHTML = `
                <div class="vote-header">
                    <div class="party-name">
                        <i class="${icon}"></i> ${label}
                    </div>
                    <div class="percentage-badge">${percent}%</div>
                </div>
                <div class="vote-count">
                    <span class="count-main">${formatted.main.toLocaleString()}</span>
                    <span class="count-unit">${formatted.unit}</span>
                    ${formatted.sub ? `<span class="count-unit">${formatted.sub}</span>` : ''}
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${percent}%"></div>
                </div>
                <div class="meta-info">
                    <span>得票數：${count.toLocaleString()}</span>
                    <span>通過門檻：${totalRefVotes > 20000 && count > totalRefVotes * 0.5 ? '✓ 達成' : '✗ 未達成'}</span>
                </div>
            `;
            refContainer.appendChild(item);
        });
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    updateResults();
    // 每 5 秒更新一次數據
    setInterval(updateResults, 5000);
});

// 如果需要手動刷新功能
function refreshResults() {
    updateResults();
}